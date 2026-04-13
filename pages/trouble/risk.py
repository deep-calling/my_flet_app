"""风险分析四合一 — 对象 / 单元 / 事件 / 措施 列表 + 详情"""

from __future__ import annotations

import flet as ft

from services import trouble_service as ts
from components.list_page import build_list_page
from components.detail_page import build_detail_page, detail_section
from components.form_fields import readonly_field
from components.status_badge import status_badge


def _kv_row(label: str, value: str, value_max_lines: int = 2) -> ft.Control:
    """列表项中 "标签：值" 单行。标签定宽，值省略溢出。"""
    return ft.Row(
        controls=[
            ft.Text(
                f"{label}：",
                size=13, color=ft.colors.GREY_700, width=110,
                no_wrap=True,
            ),
            ft.Text(
                value or "-",
                size=13, color=ft.colors.GREY_800,
                expand=True, max_lines=value_max_lines,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
        ],
        spacing=4,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )


# ============================================================
# 风险分析对象
# ============================================================

async def build_risk_object_view(page: ft.Page) -> ft.View:
    """风险分析对象列表"""

    async def _load(pn, ps, filters):
        result = await ts.get_risk_object_list({
            "pageNo": pn, "pageSize": ps, **filters,
        })
        return {
            "records": result.get("records", []) if isinstance(result, dict) else [],
            "total": result.get("total", 0) if isinstance(result, dict) else 0,
        }

    def _build_item(item: dict) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        item.get("riskAnalysisObjectName", ""),
                        size=15, weight=ft.FontWeight.W_500,
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Row([
                        ft.Text(
                            f"类型：{item.get('riskAnalysisObjectType_dictText', '-')}",
                            size=12, color=ft.colors.GREY_500, expand=True,
                        ),
                        status_badge(item.get("majorHazardLevel_dictText", ""))
                        if item.get("majorHazardLevel_dictText") else ft.Container(),
                    ]),
                    ft.Text(
                        f"工艺类型：{item.get('processType_dictText', '-')}",
                        size=12, color=ft.colors.GREY_500,
                    ),
                ],
                spacing=4,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200)),
        )

    async def _on_click(item):
        await page.go_async(f"/trouble/risk_analysis_object/detail?id={item['id']}")

    return await build_list_page(
        page,
        title="风险分析对象",
        on_load_data=_load,
        build_item=_build_item,
        on_item_click=_on_click,
        search_hint="搜索风险对象",
    )


async def build_risk_object_detail_view(page: ft.Page, record_id: str) -> ft.View:
    """风险分析对象详情"""

    def _build(data: dict) -> ft.Control:
        return detail_section("基本信息", [
            readonly_field("所属部门", data.get("sysOrgCode_dictText", data.get("sysOrgCode", ""))),
            readonly_field("责任人", data.get("dutyPerson_dictText", data.get("dutyPerson", ""))),
            readonly_field("危险源编码", data.get("hazardCode", "")),
            readonly_field("风险分析对象名称", data.get("riskAnalysisObjectName", "")),
            readonly_field("风险分析对象类型", data.get("riskAnalysisObjectType_dictText", "")),
            readonly_field("风险等级", data.get("majorHazardLevel_dictText", "")),
            readonly_field("工艺类型", data.get("processType_dictText", "")),
            readonly_field("分析单元数", data.get("analyticalUnitNumber", "")),
            readonly_field("备注", data.get("remark", "")),
        ])

    return await build_detail_page(
        page, title="风险对象详情", record_id=record_id,
        on_load_data=ts.get_risk_object_detail, build_content=_build,
    )


# ============================================================
# 风险分析单元
# ============================================================

async def build_risk_unit_view(page: ft.Page) -> ft.View:
    """风险分析单元列表"""

    async def _load(pn, ps, filters):
        result = await ts.get_risk_unit_list({
            "pageNo": pn, "pageSize": ps, **filters,
        })
        return {
            "records": result.get("records", []) if isinstance(result, dict) else [],
            "total": result.get("total", 0) if isinstance(result, dict) else 0,
        }

    def _build_item(item: dict) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                controls=[
                    _kv_row("风险分析对象名称", item.get("riskAnalysisObjectId_dictText", "")),
                    _kv_row("风险分析单元名称", item.get("riskAnalysisUnitName", "")),
                ],
                spacing=6,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200)),
        )

    async def _on_click(item):
        await page.go_async(f"/trouble/risk_analysis_unit/detail?id={item['id']}")

    return await build_list_page(
        page, title="风险分析单元",
        on_load_data=_load, build_item=_build_item,
        on_item_click=_on_click, search_hint="搜索风险单元",
    )


async def build_risk_unit_detail_view(page: ft.Page, record_id: str) -> ft.View:
    """风险分析单元详情"""

    def _build(data: dict) -> ft.Control:
        return detail_section("基本信息", [
            readonly_field("风险分析对象名称", data.get("riskAnalysisObjectId_dictText", "")),
            readonly_field("所属部门", data.get("sysOrgCode_dictText", data.get("sysOrgCode", ""))),
            readonly_field("责任人", data.get("dutyPerson_dictText", data.get("dutyPerson", ""))),
            readonly_field("风险分析单元名称", data.get("riskAnalysisUnitName", "")),
        ])

    return await build_detail_page(
        page, title="风险单元详情", record_id=record_id,
        on_load_data=ts.get_risk_unit_detail, build_content=_build,
    )


# ============================================================
# 风险分析事件
# ============================================================

async def build_risk_event_view(page: ft.Page) -> ft.View:
    """风险分析事件列表"""

    async def _load(pn, ps, filters):
        result = await ts.get_risk_event_list({
            "pageNo": pn, "pageSize": ps, **filters,
        })
        return {
            "records": result.get("records", []) if isinstance(result, dict) else [],
            "total": result.get("total", 0) if isinstance(result, dict) else 0,
        }

    def _build_item(item: dict) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                controls=[
                    _kv_row("风险分析单元名称", item.get("riskAnalysisUnitId_dictText", "")),
                    _kv_row(
                        "风险分析事件名称",
                        item.get("riskEventName", item.get("riskAnalysisEventName", "")),
                    ),
                ],
                spacing=6,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200)),
        )

    return await build_list_page(
        page, title="风险分析事件",
        on_load_data=_load, build_item=_build_item,
        search_hint="搜索风险事件",
    )


# ============================================================
# 风险管控措施
# ============================================================

async def build_risk_measure_view(page: ft.Page) -> ft.View:
    """风险管控措施列表"""

    async def _load(pn, ps, filters):
        result = await ts.get_risk_measure_list({
            "pageNo": pn, "pageSize": ps, **filters,
        })
        return {
            "records": result.get("records", []) if isinstance(result, dict) else [],
            "total": result.get("total", 0) if isinstance(result, dict) else 0,
        }

    def _build_item(item: dict) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                controls=[
                    _kv_row("风险分析单元名称", item.get("riskAnalysisUnitId_dictText", "")),
                    _kv_row("风险分析事件名称", item.get("riskAnalysisEventId_dictText", "")),
                    _kv_row("管控措施描述", item.get("manageMeasureDesc", ""), value_max_lines=3),
                    _kv_row("隐患排查内容", item.get("hiddenDangerCheckContent", ""), value_max_lines=3),
                ],
                spacing=6,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200)),
        )

    async def _on_click(item):
        await page.go_async(f"/trouble/risk_manage_measure/detail?id={item['id']}")

    return await build_list_page(
        page, title="风险管控措施",
        on_load_data=_load, build_item=_build_item,
        on_item_click=_on_click, search_hint="搜索管控措施",
    )


async def build_risk_measure_detail_view(page: ft.Page, record_id: str) -> ft.View:
    """风险管控措施详情"""

    def _build(data: dict) -> ft.Control:
        return detail_section("基本信息", [
            readonly_field("风险分析单元名称", data.get("riskAnalysisUnitId_dictText", "")),
            readonly_field("风险分析事件名称", data.get("riskAnalysisEventId_dictText", "")),
            readonly_field("管控方式", data.get("manageType_dictText", "")),
            readonly_field("管控措施分类1", data.get("manageMeasureType1_dictText", "")),
            readonly_field("管控措施分类2", data.get("manageMeasureType2_dictText", "")),
            readonly_field("管控措施分类3", data.get("manageMeasureType3", "")),
            readonly_field("管控措施描述", data.get("manageMeasureDesc", "")),
            readonly_field("隐患排查内容", data.get("hiddenDangerCheckContent", "")),
        ])

    return await build_detail_page(
        page, title="管控措施详情", record_id=record_id,
        on_load_data=ts.get_risk_measure_detail, build_content=_build,
    )
