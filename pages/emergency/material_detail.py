"""应急物资 — 详情页"""

from __future__ import annotations

import flet as ft

from components.detail_page import build_detail_page, detail_section
from components.form_fields import readonly_field
from services import emergency_service as es


async def build_material_detail_view(page: ft.Page, record_id: str) -> ft.View:
    """应急物资详情"""

    def _build_content(data: dict) -> ft.Control:
        return ft.Column(
            spacing=0,
            controls=[
                detail_section("基本信息", [
                    readonly_field("物资名称", data.get("materialName", "")),
                    readonly_field("物资编号", data.get("materialNumber", "")),
                    readonly_field("物资用途", data.get("materialPurpose_dictText", "")),
                    readonly_field("物资型号", data.get("materialModel", "")),
                    readonly_field("负责人", data.get("leader_dictText", "")),
                    readonly_field("负责部门", data.get("leaderDepart_dictText", "")),
                    readonly_field("物资分类", data.get("materialType_dictText", "")),
                    readonly_field("存放位置", data.get("storageLocation", "")),
                    readonly_field("存储数量", str(data.get("storageAmount", ""))),
                    readonly_field("生产日期", data.get("manufactureDate", "")),
                    readonly_field("使用期限(天)", str(data.get("usefulLife", ""))),
                    readonly_field("生命周期", data.get("lifeCycle_dictText", "")),
                    readonly_field("物资状态", data.get("materialStatus_dictText", "")),
                    readonly_field("投用日期", data.get("commissionDate", "")),
                    readonly_field("检查周期(天)", str(data.get("inspectionCycle", ""))),
                    readonly_field("保养周期(天)", str(data.get("maintenanceCycle", ""))),
                    readonly_field("使用说明", data.get("instructions", "")),
                ]),
            ],
        )

    return await build_detail_page(
        page,
        title="应急物资详情",
        record_id=record_id,
        on_load_data=es.get_material_detail,
        build_content=_build_content,
    )
