"""在线考试 — 考试列表（待处理/已完成 Tab）"""

from __future__ import annotations

from datetime import datetime

import flet as ft

from components.scroll_helper import apply_no_bounce

from services import train_service as ts
from components.status_badge import status_badge


async def build_test_view(page: ft.Page) -> ft.View:
    """在线考试列表页"""

    current_tab = [0]  # 0=待处理(type=1), 1=已完成(type=2)
    current_page_no = [1]
    page_size = 10
    items_data: list[dict] = []
    is_loading = [False]
    search_text = [""]

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

    def _is_exam_started(begin_date: str) -> bool:
        """判断考试是否已开始"""
        if not begin_date:
            return True
        try:
            dt = datetime.strptime(begin_date.replace("-", "/"), "%Y/%m/%d %H:%M:%S")
            return datetime.now() >= dt
        except Exception:
            return True

    async def _load_data(reset: bool = False):
        if is_loading[0]:
            return
        is_loading[0] = True
        loading_ring.visible = True
        await page.update_async()

        if reset:
            current_page_no[0] = 1
            items_data.clear()
            list_column.controls.clear()

        try:
            tab_type = "1" if current_tab[0] == 0 else "2"
            params: dict = {
                "type": tab_type,
                "pageNo": current_page_no[0],
                "pageSize": page_size,
            }
            if search_text[0]:
                params["name"] = search_text[0]

            result = await ts.get_exam_list(params)
            records = result.get("records", []) if isinstance(result, dict) else []
            total = result.get("total", 0) if isinstance(result, dict) else 0

            for item in records:
                items_data.append(item)
                ctrl = _build_item(item)

                def _make_click(data):
                    async def _click(e):
                        if current_tab[0] == 0:
                            # 待处理 — 检查考试是否开始
                            if not _is_exam_started(data.get("beginDate", "")):
                                page.snack_bar = ft.SnackBar(
                                    ft.Text("当前考试尚未开始"), open=True
                                )
                                await page.update_async()
                                return
                            await page.go_async(
                                f"/train/exam?id={data.get('testPaperId', '')}"
                                f"&answerMethod={data.get('answerMethod', '')}"
                                f"&examId={data.get('examId', '')}&type=2"
                            )
                        else:
                            # 已完成 — 查看结果
                            await page.go_async(
                                f"/train/details?examId={data.get('examId', '')}"
                                f"&type=2&resultId={data.get('resultId', '')}"
                            )
                    return _click

                list_column.controls.append(
                    ft.Container(content=ctrl, on_click=_make_click(item), ink=True)
                )

            has_more = len(items_data) < total
            load_more_btn.visible = has_more
            if has_more:
                load_more_btn.content = ft.TextButton(
                    "加载更多", on_click=_on_load_more,
                    style=ft.ButtonStyle(color=ft.colors.BLUE),
                )
            empty_widget.visible = len(items_data) == 0
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"加载失败：{ex}"), open=True)

        is_loading[0] = False
        loading_ring.visible = False
        await page.update_async()

    async def _on_load_more(e):
        current_page_no[0] += 1
        await _load_data(reset=False)

    async def _on_search(e):
        search_text[0] = e.control.value.strip()
        await _load_data(reset=True)

    def _build_item(item: dict) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        item.get("examName", ""),
                        size=15, weight=ft.FontWeight.W_500,
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(
                        f"答题时间：{item.get('answerTime', '-')} 分钟",
                        size=13, color=ft.colors.GREY_600,
                    ),
                    ft.Row(controls=[
                        ft.Text(
                            f"开始：{item.get('beginDate', '-')}",
                            size=12, color=ft.colors.GREY_500, expand=True,
                        ),
                        ft.Text(
                            f"结束：{item.get('endDate', '-')}",
                            size=12, color=ft.colors.GREY_500,
                        ),
                    ]),
                ],
                spacing=4,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200)),
        )

    async def _on_tab_change(e):
        current_tab[0] = e.control.selected_index
        await _load_data(reset=True)

    tabs = ft.Tabs(
        selected_index=0,
        on_change=_on_tab_change,
        tabs=[ft.Tab(text="待处理"), ft.Tab(text="已完成")],
        label_color=ft.colors.BLUE,
        unselected_label_color=ft.colors.GREY_600,
        indicator_color=ft.colors.BLUE,
        divider_color=ft.colors.GREY_200,
    )

    search_field = ft.TextField(
        hint_text="搜索考试名称",
        prefix_icon=ft.icons.SEARCH,
        on_submit=_on_search,
        border_color=ft.colors.GREY_300,
        focused_border_color=ft.colors.BLUE,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=6),
        text_size=14, height=40,
    )
    search_bar = ft.Container(
        content=search_field,
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        bgcolor=ft.colors.WHITE,
    )

    scroll_content = ft.ListView(
        controls=[
            list_column,
            ft.Container(
                content=ft.Row([loading_ring], alignment=ft.MainAxisAlignment.CENTER),
                padding=10,
            ),
            load_more_btn,
            empty_widget,
        ],
        expand=True,
    )
    apply_no_bounce(scroll_content)

    body = ft.Column(controls=[tabs, search_bar, scroll_content], spacing=0, expand=True)

    view = ft.View(
        route="/train/test",
        appbar=ft.AppBar(title=ft.Text("在线考试"), bgcolor=ft.colors.WHITE),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    await _load_data(reset=True)
    return view
