"""应急物资 — 列表页"""

from __future__ import annotations

import flet as ft

from components.list_page import build_list_page
from services import emergency_service as es


async def build_material_list_view(page: ft.Page) -> ft.View:
    """应急物资列表"""

    # 加载字典
    material_type_opts: list[dict] = []
    material_status_opts: list[dict] = []
    try:
        types = await es.get_dict_items("material_type")
        material_type_opts = [{"text": i["text"], "value": str(i["value"])} for i in types]
        statuses = await es.get_dict_items("material_status")
        material_status_opts = [{"text": i["text"], "value": str(i["value"])} for i in statuses]
    except Exception:
        pass

    async def _load(page_no: int, page_size: int, filters: dict) -> dict:
        params: dict = {"pageNo": page_no, "pageSize": page_size}
        if filters.get("keyword"):
            params["materialName"] = filters["keyword"]
        if filters.get("materialType"):
            params["materialType"] = filters["materialType"]
        if filters.get("materialStatus"):
            params["materialStatus"] = filters["materialStatus"]
        return await es.get_material_list(params)

    def _build_item(item: dict) -> ft.Control:
        return ft.Container(
            bgcolor=ft.colors.WHITE,
            border_radius=8,
            padding=ft.padding.all(14),
            margin=ft.margin.only(left=12, right=12, top=8),
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Text(item.get("materialName", ""), weight=ft.FontWeight.W_500, size=15),
                    ft.Row([
                        ft.Text(f"物资编号: {item.get('materialNumber', '-')}", size=13, color=ft.colors.GREY_600),
                        ft.Text(f"物资用途: {item.get('materialPurpose_dictText', '-')}", size=13, color=ft.colors.GREY_600),
                    ]),
                    ft.Text(f"物资分类: {item.get('materialType_dictText', '-')}", size=13, color=ft.colors.GREY_600),
                    ft.Text(f"物资状态: {item.get('materialStatus_dictText', '-')}", size=13, color=ft.colors.GREY_600),
                    ft.Text(f"生产日期: {item.get('manufactureDate', '-')}", size=13, color=ft.colors.GREY_600),
                    ft.Text(f"投用日期: {item.get('commissionDate', '-')}", size=13, color=ft.colors.GREY_600),
                ],
            ),
        )

    async def _on_click(item: dict):
        page.go(f"/emergency/material_detail?id={item['id']}")

    return await build_list_page(
        page,
        title="应急物资管理",
        on_load_data=_load,
        build_item=_build_item,
        on_item_click=_on_click,
        search_hint="搜索物资名称",
        filters=[
            {"key": "materialType", "label": "物资分类", "options": material_type_opts},
            {"key": "materialStatus", "label": "物资状态", "options": material_status_opts},
        ],
    )
