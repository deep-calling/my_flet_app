"""视频监控 — 摄像头列表"""

from __future__ import annotations

import flet as ft

from components.list_page import build_list_page
from services import record_service as rs


async def build_camera_list_view(page: ft.Page) -> ft.View:
    """摄像头列表"""

    async def _load(page_no: int, page_size: int, filters: dict) -> dict:
        params: dict = {"pageNo": page_no, "pageSize": page_size}
        if filters.get("keyword"):
            params["name"] = filters["keyword"]
        return await rs.get_camera_list(params)

    def _build_item(item: dict) -> ft.Control:
        return ft.Container(
            bgcolor=ft.colors.WHITE,
            border_radius=8,
            padding=ft.padding.all(14),
            margin=ft.margin.only(left=12, right=12, top=8),
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Text(f"摄像头名称: {item.get('name', '-')}", size=14, color=ft.colors.BLACK87),
                    ft.Text(f"摄像头编码: {item.get('code', '-')}", size=13, color=ft.colors.GREY_600),
                ],
            ),
        )

    async def _on_click(item: dict):
        page.go(f"/camera/detail?id={item.get('id', '')}")

    return await build_list_page(
        page,
        title="视频监控",
        on_load_data=_load,
        build_item=_build_item,
        on_item_click=_on_click,
        search_hint="搜索摄像头",
    )
