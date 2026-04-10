"""线下培训 — 列表页（待签到/已完成 Tab）+ 详情签到页"""

from __future__ import annotations

import flet as ft

from services import train_service as ts
from components.detail_page import build_detail_page, detail_section
from components.form_fields import readonly_field
from components.status_badge import status_badge


# ============================================================
# 线下培训列表
# ============================================================

async def build_offline_train_view(page: ft.Page) -> ft.View:
    """线下培训列表：待签到 / 已完成 两个 Tab"""

    current_tab = [0]  # 0=待签到(type=1), 1=已完成(type=2)
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

            result = await ts.get_offline_train_list(params)
            records = result.get("records", []) if isinstance(result, dict) else []
            total = result.get("total", 0) if isinstance(result, dict) else 0

            for item in records:
                items_data.append(item)
                ctrl = _build_item(item)

                def _make_click(data):
                    async def _click(e):
                        sign = data.get("sign", "")
                        await page.go_async(
                            f"/train/offline/detail?id={data.get('trainingId', '')}&sign={sign}"
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
        sign = str(item.get("sign", ""))
        sign_text = "未签到" if sign == "1" else "已签到"
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(controls=[
                        ft.Text(
                            item.get("name", ""),
                            size=15, weight=ft.FontWeight.W_500,
                            expand=True, max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        status_badge(sign_text),
                    ]),
                    ft.Text(f"培训日期：{item.get('trainingDate', '-')}", size=13, color=ft.colors.GREY_600),
                    ft.Row(controls=[
                        ft.Text(f"学时：{item.get('classHours', '-')}", size=12, color=ft.colors.GREY_500, expand=True),
                        ft.Text(f"地点：{item.get('place', '-')}", size=12, color=ft.colors.GREY_500),
                    ]),
                ],
                spacing=4,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200)),
        )

    # Tab 栏
    async def _on_tab_change(e):
        current_tab[0] = e.control.selected_index
        await _load_data(reset=True)

    tabs = ft.Tabs(
        selected_index=0,
        on_change=_on_tab_change,
        tabs=[ft.Tab(text="待签到"), ft.Tab(text="已完成")],
        label_color=ft.colors.BLUE,
        unselected_label_color=ft.colors.GREY_600,
        indicator_color=ft.colors.BLUE,
        divider_color=ft.colors.GREY_200,
    )

    # 搜索栏
    search_field = ft.TextField(
        hint_text="搜索培训名称",
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

    body = ft.Column(controls=[tabs, search_bar, scroll_content], spacing=0, expand=True)

    view = ft.View(
        route="/train/offline",
        appbar=ft.AppBar(title=ft.Text("线下培训"), bgcolor=ft.colors.WHITE),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    await _load_data(reset=True)
    return view


# ============================================================
# 培训详情 + 签到
# ============================================================

async def build_offline_train_detail_view(
    page: ft.Page, training_id: str, sign: str = ""
) -> ft.View:
    """线下培训详情页，含签到按钮"""

    async def _load(rid: str) -> dict:
        return await ts.get_training_detail(rid)

    def _build_content(data: dict) -> ft.Control:
        return ft.Column(
            controls=[
                detail_section("培训信息", [
                    readonly_field("培训名称", data.get("pxmc", "")),
                    readonly_field("培训学时", str(data.get("pxxs", ""))),
                    readonly_field("培训日期", data.get("pxrq", "")),
                    readonly_field("培训单位", data.get("pxdw", "")),
                    readonly_field("培训讲师", data.get("pxjs", "")),
                    readonly_field("及格分数", str(data.get("jgfs", ""))),
                    readonly_field("培训地点", data.get("pxdd", "")),
                    readonly_field("考核单位", data.get("khdw", "")),
                    readonly_field("培训费用", str(data.get("pxfy", ""))),
                ]),
                detail_section("培训简介", [
                    ft.Container(
                        content=ft.Text(data.get("pxjj", "暂无"), size=14, color=ft.colors.GREY_700),
                        padding=ft.padding.symmetric(horizontal=16, vertical=10),
                        bgcolor=ft.colors.WHITE,
                    ),
                ]),
            ],
            spacing=0,
        )

    # 签到按钮
    actions: list[dict] = []
    if sign == "1":
        async def _on_sign(e):
            try:
                await ts.sign_training(training_id)
                page.snack_bar = ft.SnackBar(ft.Text("签到成功"), open=True)
                await page.update_async()
                # 返回上一页
                page.views.pop()
                await page.update_async()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"签到失败：{ex}"), open=True)
                await page.update_async()

        actions = [{"label": "签到", "on_click": _on_sign, "style": "primary"}]

    return await build_detail_page(
        page,
        title="培训详情",
        record_id=training_id,
        on_load_data=_load,
        build_content=_build_content,
        actions=actions,
    )
