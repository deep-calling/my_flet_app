"""应急队伍 — 列表页"""

from __future__ import annotations

import flet as ft

from components.list_page import build_list_page
from services import emergency_service as es
from utils.logger import get_logger

log = get_logger("team_list")


async def build_team_list_view(page: ft.Page) -> ft.View:
    """应急队伍列表"""

    # 加载字典
    ranks_level_opts: list[dict] = []
    try:
        levels = await es.get_dict_items("ranks_level")
        ranks_level_opts = [{"text": i["text"], "value": str(i["value"])} for i in levels]
    except Exception:
        log.debug("swallowed exception", exc_info=True)

    async def _load(page_no: int, page_size: int, filters: dict) -> dict:
        params: dict = {"pageNo": page_no, "pageSize": page_size}
        if filters.get("keyword"):
            params["ranksName"] = filters["keyword"]
        if filters.get("ranksLevel"):
            params["ranksLevel"] = filters["ranksLevel"]
        return await es.get_team_list(params)

    def _build_item(item: dict) -> ft.Control:
        return ft.Container(
            bgcolor=ft.colors.WHITE,
            border_radius=8,
            padding=ft.padding.all(14),
            margin=ft.margin.only(left=12, right=12, top=8),
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Text(item.get("ranksName", ""), weight=ft.FontWeight.W_500, size=15),
                    ft.Row([
                        ft.Text(f"队伍级别: {item.get('ranksLevel_dictText', '-')}", size=13, color=ft.colors.GREY_600),
                        ft.Text(f"负责人: {item.get('ranksLeader_dictText', '-')}", size=13, color=ft.colors.GREY_600),
                    ]),
                    ft.Text(f"关联应急预案: {item.get('emerPlanId_dictText', '-')}", size=13, color=ft.colors.GREY_600),
                ],
            ),
        )

    async def _on_click(item: dict):
        page.go(f"/emergency/team_detail?id={item['id']}")

    return await build_list_page(
        page,
        title="应急队伍管理",
        on_load_data=_load,
        build_item=_build_item,
        on_item_click=_on_click,
        search_hint="搜索队伍名称",
        filters=[
            {"key": "ranksLevel", "label": "队伍级别", "options": ranks_level_opts},
        ],
    )
