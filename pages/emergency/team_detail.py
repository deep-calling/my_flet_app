"""应急队伍 — 详情页"""

from __future__ import annotations

import flet as ft

from components.detail_page import build_detail_page, detail_section
from components.form_fields import readonly_field
from services import emergency_service as es


async def build_team_detail_view(page: ft.Page, record_id: str) -> ft.View:
    """应急队伍详情"""

    def _build_content(data: dict) -> ft.Control:
        return ft.Column(
            spacing=0,
            controls=[
                detail_section("基本信息", [
                    readonly_field("队伍名称", data.get("ranksName", "")),
                    readonly_field("队伍级别", data.get("ranksLevel_dictText", "")),
                    readonly_field("队伍负责人", data.get("ranksLeader_dictText", "")),
                    readonly_field("负责人部门", data.get("leaderDepart_dictText", "")),
                    readonly_field("负责人手机", data.get("leaderPhone", "")),
                    readonly_field("固定电话", data.get("leaderLinePhone", "")),
                    readonly_field("关联应急预案", data.get("emerPlanId_dictText", "")),
                    readonly_field("备注", data.get("remarks", "")),
                ]),
            ],
        )

    return await build_detail_page(
        page,
        title="应急队伍详情",
        record_id=record_id,
        on_load_data=es.get_team_detail,
        build_content=_build_content,
    )
