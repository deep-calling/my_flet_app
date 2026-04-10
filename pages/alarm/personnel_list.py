"""人员定位报警 — 列表页"""

from __future__ import annotations

import flet as ft

from components.list_page import build_list_page
from services import alarm_service as als


async def build_personnel_alarm_view(page: ft.Page) -> ft.View:
    """人员定位报警列表，支持待处理/所有切换"""

    current_tab = [0]  # 0=待处理, 1=所有

    async def _load(page_no: int, page_size: int, filters: dict) -> dict:
        params: dict = {"pageNo": page_no, "pageSize": page_size}
        if current_tab[0] == 0:
            params["alarmStatus"] = "0"
        return await als.get_person_alarm_list(params)

    def _build_item(item: dict) -> ft.Control:
        return ft.Container(
            bgcolor=ft.colors.WHITE,
            border_radius=8,
            padding=ft.padding.all(14),
            margin=ft.margin.only(left=12, right=12, top=8),
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Text(f"报警类型: {item.get('type_dictText', '-')}", size=13, color=ft.colors.GREY_700),
                    ft.Text(f"人员姓名: {item.get('peopleName', '-')}", size=13, color=ft.colors.GREY_600),
                    ft.Text(f"人员类型: {item.get('peopleType_dictText', '-')}", size=13, color=ft.colors.GREY_600),
                    ft.Text(f"报警时间: {item.get('alarmTime', '-')}", size=13, color=ft.colors.GREY_600),
                ],
            ),
        )

    async def _on_click(item: dict):
        page.go(f"/alarm/personnel_detail?alarmId={item['id']}")

    # 先构建默认列表视图
    view = await build_list_page(
        page,
        title="人员定位",
        on_load_data=_load,
        build_item=_build_item,
        on_item_click=_on_click,
        show_search=False,
    )

    # 在搜索栏位置插入 Tab 栏
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[ft.Tab(text="待处理"), ft.Tab(text="所有")],
        height=42,
    )

    async def _on_tab_change(e):
        current_tab[0] = tabs.selected_index
        # 触发重新搜索 — 通过重建 view
        page.go(page.route)

    tabs.on_change = _on_tab_change

    # 将 tab 插在 body 最前面
    body_col = view.controls[0]  # ft.Column
    body_col.controls.insert(0, ft.Container(
        content=tabs,
        bgcolor=ft.colors.WHITE,
    ))

    return view
