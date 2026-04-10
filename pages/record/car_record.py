"""车辆进出记录 — 列表页"""

from __future__ import annotations

import flet as ft

from components.list_page import build_list_page
from services import record_service as rs


async def build_car_record_view(page: ft.Page) -> ft.View:
    """车辆进出记录列表"""

    async def _load(page_no: int, page_size: int, filters: dict) -> dict:
        return await rs.get_car_record_list(
            {"pageNo": page_no, "pageSize": page_size}
        )

    def _build_item(item: dict) -> ft.Control:
        return ft.Container(
            bgcolor=ft.colors.WHITE,
            border_radius=8,
            padding=ft.padding.all(14),
            margin=ft.margin.only(left=12, right=12, top=8),
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Text(f"进出时间: {item.get('accessTime', '-')}", size=13, color=ft.colors.GREY_700),
                    ft.Row([
                        ft.Text(f"车牌号: {item.get('plateNo', '-')}", size=13, color=ft.colors.GREY_600),
                        ft.Text(f"司机: {item.get('driver', '-')}", size=13, color=ft.colors.GREY_600),
                    ]),
                    ft.Row([
                        ft.Text(f"电话: {item.get('phone', '-')}", size=13, color=ft.colors.GREY_600),
                        ft.Text(f"进出区分: {item.get('accessAction', '-')}", size=13, color=ft.colors.GREY_600),
                    ]),
                    ft.Text(f"车道: {item.get('laneName', '-')}", size=13, color=ft.colors.GREY_600),
                ],
            ),
        )

    return await build_list_page(
        page,
        title="车辆进出信息",
        on_load_data=_load,
        build_item=_build_item,
        show_search=False,
    )
