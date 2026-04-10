"""应急演练计划 — 详情页"""

from __future__ import annotations

import flet as ft

from components.detail_page import build_detail_page, detail_section
from components.form_fields import readonly_field
from services import emergency_service as es


async def build_plan_detail_view(page: ft.Page, record_id: str) -> ft.View:
    """演练计划详情"""

    def _build_content(data: dict) -> ft.Control:
        return ft.Column(
            spacing=0,
            controls=[
                detail_section("基本信息", [
                    readonly_field("演练名称", data.get("drillName", "")),
                    readonly_field("演练地点", data.get("drillPlace", "")),
                    readonly_field("主办部门", data.get("hostDepart_dictText", "")),
                    readonly_field("演练方式", data.get("drillMode_dictText", "")),
                    readonly_field("应急预案", data.get("emerPlan_dictText", "")),
                    readonly_field("演练级别", data.get("drillLevel_dictText", "")),
                    readonly_field("计划制定日期", data.get("planCustomDate", "")),
                    readonly_field("计划演练日期", data.get("planDrillDate", "")),
                    readonly_field("计划制定人", data.get("planCustomizer_dictText", "")),
                    readonly_field("备注", data.get("remarks", "")),
                ]),
                detail_section("演练计划", [
                    readonly_field("实际演练日期", data.get("actualDrillDate", "")),
                    readonly_field("演练实施人员", data.get("drillPerson_dictText", "")),
                    readonly_field("主要参演人员", data.get("mainParticipants_dictText", "")),
                    readonly_field("其他参演部门", data.get("drillDepart_dictText", "")),
                    readonly_field("演练内容", data.get("drillContent", "")),
                ]),
            ],
        )

    return await build_detail_page(
        page,
        title="应急演练计划详情",
        record_id=record_id,
        on_load_data=es.get_plan_detail,
        build_content=_build_content,
    )
