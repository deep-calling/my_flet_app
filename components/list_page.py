"""通用列表页模板 — AppBar + 搜索/筛选 + 列表 + 加载更多"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Awaitable

import flet as ft

from services.pagination import as_page
from utils.logger import get_logger

log = get_logger("list_page")


async def build_list_page(
    page: ft.Page,
    *,
    title: str,
    on_load_data: Callable[[int, int, dict], Awaitable[dict]],
    build_item: Callable[[dict], ft.Control],
    filters: list[dict] | None = None,
    search_hint: str = "搜索",
    show_search: bool = True,
    on_item_click: Callable[[dict], Awaitable[None]] | None = None,
    page_size: int = 15,
) -> ft.View:
    """构建通用列表页 View。

    参数:
        on_load_data: async (page_no, page_size, filters_dict) -> 分页字典 或 list
        build_item: (item_dict) -> ft.Control，渲染单个列表项
        filters: [{key, label, options: [{text, value}]}]，筛选条件
        on_item_click: async (item_dict) -> None，点击列表项
    """
    filters = filters or []

    current_page = [1]
    total_count = [0]
    items_data: list[dict] = []
    is_loading = [False]
    search_text = [""]
    filter_values: dict[str, str] = {f["key"]: "" for f in filters}

    # 跟踪当前加载任务，View pop 时由调用方 cancel
    load_task: list[asyncio.Task | None] = [None]

    list_column = ft.Column(spacing=0, expand=True)
    loading_ring = ft.ProgressRing(width=24, height=24, visible=False)
    load_more_btn = ft.Container(visible=False)

    empty_widget = ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(ft.icons.INBOX_OUTLINED, size=64, color=ft.colors.GREY_300),
                ft.Text("暂无数据", size=14, color=ft.colors.GREY_400),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        alignment=ft.alignment.center,
        padding=ft.padding.only(top=120),
        visible=False,
    )

    error_widget = ft.Container(visible=False)

    def _build_filters_dict() -> dict:
        d: dict[str, Any] = {}
        if search_text[0]:
            d["keyword"] = search_text[0]
        for k, v in filter_values.items():
            if v:
                d[k] = v
        return d

    async def _safe_update():
        try:
            await page.update_async()
        except Exception:
            log.debug("page.update_async on stale view")

    async def _do_load(reset: bool = False):
        if is_loading[0]:
            return
        is_loading[0] = True
        loading_ring.visible = True
        error_widget.visible = False
        await _safe_update()

        if reset:
            current_page[0] = 1
            items_data.clear()
            list_column.controls.clear()

        try:
            raw = await on_load_data(
                current_page[0], page_size, _build_filters_dict()
            )
            result = as_page(raw)
            records = result["records"]
            total_count[0] = result["total"]

            for item in records:
                items_data.append(item)
                item_ctrl = build_item(item)

                if on_item_click:
                    def _make_click(data):
                        async def _click(e):
                            await on_item_click(data)
                        return _click

                    item_container = ft.Container(
                        content=item_ctrl,
                        on_click=_make_click(item),
                        ink=True,
                    )
                    list_column.controls.append(item_container)
                else:
                    list_column.controls.append(item_ctrl)

            has_more = len(items_data) < total_count[0]
            load_more_btn.visible = has_more
            load_more_btn.content = ft.TextButton(
                text="加载更多",
                on_click=_on_load_more,
                style=ft.ButtonStyle(color=ft.colors.BLUE),
            )

            empty_widget.visible = len(items_data) == 0
            error_widget.visible = False

        except asyncio.CancelledError:
            raise
        except Exception as ex:
            log.exception("列表加载失败：%s", title)
            if not items_data:
                error_widget.visible = True
                error_widget.content = ft.Column(
                    controls=[
                        ft.Icon(ft.icons.ERROR_OUTLINE, size=48, color=ft.colors.RED_300),
                        ft.Text(f"加载失败：{ex}", size=13, color=ft.colors.GREY_600,
                                text_align=ft.TextAlign.CENTER),
                        ft.OutlinedButton(
                            "重试",
                            on_click=lambda e: page.run_task(_do_load, True),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                )
                error_widget.alignment = ft.alignment.center
                error_widget.padding = ft.padding.only(top=100)
            else:
                page.open(ft.SnackBar(ft.Text(f"加载失败：{ex}")))

        finally:
            is_loading[0] = False
            loading_ring.visible = False
            await _safe_update()

    async def _on_load_more(e):
        current_page[0] += 1
        await _do_load(reset=False)

    async def _on_search(e):
        search_text[0] = e.control.value.strip()
        await _do_load(reset=True)

    # --- 搜索栏 ---
    search_bar = ft.Container(visible=False)
    if show_search:
        search_field = ft.TextField(
            hint_text=search_hint,
            prefix_icon=ft.icons.SEARCH,
            on_submit=_on_search,
            border_color=ft.colors.GREY_300,
            focused_border_color=ft.colors.BLUE,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=6),
            text_size=14,
            height=40,
        )
        search_bar = ft.Container(
            content=search_field,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor=ft.colors.WHITE,
        )

    # --- 筛选栏 ---
    filter_bar = ft.Container(visible=False)
    if filters:
        filter_controls: list[ft.Control] = []
        for f in filters:
            def _make_filter_change(key):
                async def _on_change(e):
                    filter_values[key] = e.control.value or ""
                    await _do_load(reset=True)
                return _on_change

            dd = ft.Dropdown(
                hint_text=f["label"],
                options=[ft.dropdown.Option(key=o["value"], text=o["text"]) for o in f.get("options", [])],
                on_change=_make_filter_change(f["key"]),
                border_color=ft.colors.GREY_300,
                content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
                text_size=13,
                height=38,
                expand=True,
            )
            filter_controls.append(dd)

        filter_bar = ft.Container(
            content=ft.Row(controls=filter_controls, spacing=8),
            padding=ft.padding.symmetric(horizontal=12, vertical=4),
            bgcolor=ft.colors.WHITE,
        )

    from components.scroll_helper import apply_no_bounce

    async def _on_list_scroll(e: ft.OnScrollEvent):
        pixels = e.pixels or 0
        max_ext = e.max_scroll_extent or 0
        if (
            max_ext > 0
            and max_ext - pixels <= 80
            and load_more_btn.visible
            and not is_loading[0]
        ):
            await _on_load_more(e)

    scroll_content = ft.ListView(
        controls=[
            list_column,
            ft.Container(
                content=ft.Row(
                    controls=[loading_ring],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=10,
            ),
            load_more_btn,
            empty_widget,
            error_widget,
        ],
        expand=True,
        padding=0,
        on_scroll=_on_list_scroll,
        on_scroll_interval=100,
    )
    apply_no_bounce(scroll_content)

    body = ft.Column(
        controls=[search_bar, filter_bar, scroll_content],
        spacing=0,
        expand=True,
    )

    view = ft.View(
        route=f"/{title}",
        appbar=ft.AppBar(title=ft.Text(title), bgcolor=ft.colors.WHITE),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    view.reload = lambda: _do_load(reset=True)

    async def _kickoff():
        try:
            await _do_load(reset=True)
        except asyncio.CancelledError:
            log.debug("list first-load cancelled: %s", title)

    # 记录任务句柄，暴露给外部用于取消
    load_task[0] = page.run_task(_kickoff)
    view.data = {"load_task": load_task, "type": "list_page"}

    return view
