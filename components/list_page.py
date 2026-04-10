"""通用列表页模板 — AppBar + 搜索/筛选 + 列表 + 加载更多"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Awaitable

import flet as ft


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
        on_load_data: async (page_no, page_size, filters_dict) -> {records: list, total: int}
        build_item: (item_dict) -> ft.Control，渲染单个列表项
        filters: [{key, label, options: [{text, value}]}]，筛选条件
        on_item_click: async (item_dict) -> None，点击列表项
    """
    filters = filters or []

    # --- 状态 ---
    current_page = [1]
    total_count = [0]
    items_data: list[dict] = []
    is_loading = [False]
    search_text = [""]
    filter_values: dict[str, str] = {f["key"]: "" for f in filters}

    # --- 控件引用 ---
    list_column = ft.Column(spacing=0, expand=True)
    loading_ring = ft.ProgressRing(width=24, height=24, visible=False)
    load_more_btn = ft.Container(visible=False)
    empty_widget = ft.Container(visible=False)

    # 空状态
    empty_content = ft.Column(
        controls=[
            ft.Icon(ft.icons.INBOX_OUTLINED, size=64, color=ft.colors.GREY_300),
            ft.Text("暂无数据", size=14, color=ft.colors.GREY_400),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=8,
    )
    empty_widget = ft.Container(
        content=empty_content,
        alignment=ft.alignment.center,
        padding=ft.padding.only(top=120),
        visible=False,
    )

    def _build_filters_dict() -> dict:
        """组装当前筛选参数"""
        d: dict[str, Any] = {}
        if search_text[0]:
            d["keyword"] = search_text[0]
        for k, v in filter_values.items():
            if v:
                d[k] = v
        return d

    async def _do_load(reset: bool = False):
        """加载数据，reset=True 则从第 1 页开始"""
        if is_loading[0]:
            return
        is_loading[0] = True
        loading_ring.visible = True
        await page.update_async()

        if reset:
            current_page[0] = 1
            items_data.clear()
            list_column.controls.clear()

        try:
            result = await on_load_data(
                current_page[0], page_size, _build_filters_dict()
            )
            records = result.get("records", [])
            total_count[0] = result.get("total", 0)

            for item in records:
                items_data.append(item)
                item_ctrl = build_item(item)

                # 包裹点击事件
                if on_item_click:
                    # 闭包捕获 item
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

            # 判断是否还有更多
            has_more = len(items_data) < total_count[0]
            load_more_btn.visible = has_more
            load_more_btn.content = ft.TextButton(
                text="加载更多",
                on_click=_on_load_more,
                style=ft.ButtonStyle(color=ft.colors.BLUE),
            )

            # 空状态
            empty_widget.visible = len(items_data) == 0

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"加载失败：{ex}"), open=True)

        is_loading[0] = False
        loading_ring.visible = False
        await page.update_async()

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
            async def _make_filter_change(key):
                async def _on_change(e):
                    filter_values[key] = e.control.value or ""
                    await _do_load(reset=True)
                return _on_change

            dd = ft.Dropdown(
                hint_text=f["label"],
                options=[ft.dropdown.Option(key=o["value"], text=o["text"]) for o in f.get("options", [])],
                on_change=await _make_filter_change(f["key"]),
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

    # --- 组装页面 ---
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
        ],
        expand=True,
        padding=0,
    )

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

    # 暴露重新加载方法，供外部调用（如 Tab 切换时）
    view.reload = lambda: _do_load(reset=True)

    # 首次加载放到异步任务中，不阻塞 View 返回
    asyncio.ensure_future(_do_load(reset=True))

    return view
