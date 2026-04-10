"""应急演练计划 — 列表页"""

from __future__ import annotations

import flet as ft

from components.list_page import build_list_page
from services import emergency_service as es


async def build_plan_list_view(page: ft.Page) -> ft.View:
    """演练计划列表"""

    # 加载字典选项
    drill_mode_opts: list[dict] = []
    drill_level_opts: list[dict] = []
    try:
        modes = await es.get_dict_items("drill_mode")
        drill_mode_opts = [{"text": i["text"], "value": str(i["value"])} for i in modes]
        levels = await es.get_dict_items("drill_level")
        drill_level_opts = [{"text": i["text"], "value": str(i["value"])} for i in levels]
    except Exception:
        pass

    async def _load(page_no: int, page_size: int, filters: dict) -> dict:
        params: dict = {"pageNo": page_no, "pageSize": page_size}
        if filters.get("keyword"):
            params["drillName"] = filters["keyword"]
        if filters.get("drillMode"):
            params["drillMode"] = filters["drillMode"]
        if filters.get("drillLevel"):
            params["drillLevel"] = filters["drillLevel"]
        return await es.get_plan_list(params)

    def _build_item(item: dict) -> ft.Control:
        return ft.Container(
            bgcolor=ft.colors.WHITE,
            border_radius=8,
            padding=ft.padding.all(14),
            margin=ft.margin.only(left=12, right=12, top=8),
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Text(item.get("drillName", ""), weight=ft.FontWeight.W_500, size=15),
                    ft.Row([
                        ft.Text(f"演练方式: {item.get('drillMode_dictText', '-')}", size=13, color=ft.colors.GREY_600),
                        ft.Text(f"演练级别: {item.get('drillLevel_dictText', '-')}", size=13, color=ft.colors.GREY_600),
                    ]),
                    ft.Text(f"计划制定日期: {item.get('planCustomDate', '-')}", size=13, color=ft.colors.GREY_600),
                    ft.Text(f"计划演练日期: {item.get('planDrillDate', '-')}", size=13, color=ft.colors.GREY_600),
                    ft.Text(f"演练地点: {item.get('drillPlace', '-')}", size=13, color=ft.colors.GREY_600),
                ],
            ),
        )

    async def _on_click(item: dict):
        page.go(f"/emergency/plan_detail?id={item['id']}")

    return await build_list_page(
        page,
        title="应急演练计划",
        on_load_data=_load,
        build_item=_build_item,
        on_item_click=_on_click,
        search_hint="搜索演练名称",
        filters=[
            {"key": "drillMode", "label": "演练方式", "options": drill_mode_opts},
            {"key": "drillLevel", "label": "演练级别", "options": drill_level_opts},
        ],
    )
