"""安全风险分区分级模块 — 路由注册

用工厂函数批量生成 8 个列表+详情页面，read 模块单独处理。
"""

from __future__ import annotations

import flet as ft

from services import security_service as ss
from components.detail_page import detail_section
from components.form_fields import readonly_field
from pages.security.common import (
    make_list_view_builder,
    make_simple_detail_view_builder,
    make_custom_detail_view_builder,
)

# ==================================================================
# 2. 应急卡 — 简单列表+详情
# ==================================================================

build_emergency_list_view = make_list_view_builder(
    title="风险应急卡",
    list_api=ss.emergency_card_list,
    list_fields=[
        ("处置卡编号", "yjczkbh"),
        ("处置卡名称", "czkmc"),
        ("关联风险点", "glfxd_dictText"),
        ("关联岗位", "gw_dictText"),
        ("关联风险分区", "fxfq_dictText"),
    ],
    detail_route="/security/emergency/detail",
)

build_emergency_detail_view = make_simple_detail_view_builder(
    title="风险应急卡",
    detail_api=ss.query_emergency_card_by_id,
    detail_fields=[
        ("应急处置卡编号", "yjczkbh"),
        ("处置卡名称", "czkmc"),
        ("关联风险点", "glfxd_dictText"),
        ("关联岗位", "gw_dictText"),
        ("关联信息", "glxx"),
        ("风险等级", "fxdj_dictText"),
        ("主要负责人", "zyzrr_dictText"),
        ("内部应急电话", "ynbyjdh"),
        ("外部应急电话", "wbyjdh"),
        ("相关附件", "xgfj"),
        ("事故特征", "sgtz"),
        ("危害描述", "whms"),
        ("工艺说明", "gysm"),
        ("步骤说明", "bzsm"),
    ],
)


# ==================================================================
# 3. 应知卡
# ==================================================================

build_know_list_view = make_list_view_builder(
    title="风险应知卡",
    list_api=ss.know_card_list,
    list_fields=[
        ("应知卡编号", "yzkbh"),
        ("关联风险点", "glfxd_dictText"),
        ("关联岗位", "gw_dictText"),
        ("关联风险分区", "fxfq_dictText"),
    ],
    detail_route="/security/know/detail",
)

build_know_detail_view = make_simple_detail_view_builder(
    title="风险应知卡",
    detail_api=ss.query_know_card_by_id,
    detail_fields=[
        ("应知卡编号", "yzkbh"),
        ("关联风险点", "glfxd_dictText"),
        ("关联岗位", "gw_dictText"),
        ("关联信息", "glxx"),
        ("关联风险分区", "fxfq_dictText"),
        ("风险等级", "fxdj_dictText"),
        ("安全警示", "aqjsbs_dictText"),
        ("相关附件", "xgfj"),
        ("主要危险有害因素", "zywlyhys"),
        ("易导致事故风险", "ydzsgfx"),
        ("风险管控措施", "fxgkcs"),
        ("应急处置对策", "yjczdc"),
    ],
)


# ==================================================================
# 4. 承诺卡
# ==================================================================

build_commitment_list_view = make_list_view_builder(
    title="风险承诺卡",
    list_api=ss.commitment_card_list,
    list_fields=[
        ("承诺卡编号", "cnkbh"),
        ("关联岗位", "glgw_dictText"),
        ("承诺人", "cnr_dictText"),
        ("主管领导", "zgld_dictText"),
    ],
    detail_route="/security/commitment/detail",
)

build_commitment_detail_view = make_simple_detail_view_builder(
    title="风险承诺卡",
    detail_api=ss.query_commitment_card_by_id,
    detail_fields=[
        ("承诺卡编号", "cnkbh"),
        ("所属部门", "shbm_dictText"),
        ("关联岗位", "glgw_dictText"),
        ("承诺人", "cnr_dictText"),
        ("主管领导", "zgld_dictText"),
        ("承诺事项", "cnsx"),
        ("相关附件", "xgfj"),
    ],
)


# ==================================================================
# 5. 管控清单
# ==================================================================

build_controls_list_view = make_list_view_builder(
    title="管控清单",
    list_api=ss.control_list,
    list_fields=[
        ("风险点编号", "fxdbh"),
        ("风险点名称", "fxdmc"),
        ("所属分区", "ssfq_dictText"),
        ("所属部门", "szbm_dictText"),
        ("风险点分类", "fxdfl_dictText"),
        ("风险等级", "fxdj_dictText"),
        ("责任人", "zrr_dictText"),
    ],
    detail_route="/security/controls/detail",
)


# ==================================================================
# 6. 辨识清单
# ==================================================================

build_identify_list_view = make_list_view_builder(
    title="辨识清单",
    list_api=ss.identify_list,
    list_fields=[
        ("风险点编号", "fxdbh"),
        ("风险点名称", "fxdmc"),
        ("所属分区", "ssfq_dictText"),
        ("所属部门", "szbm_dictText"),
        ("风险点分类", "fxdfl_dictText"),
        ("风险等级", "fxdj_dictText"),
        ("责任人", "zrr_dictText"),
    ],
    detail_route="/security/identify/detail",
)


# ------------------------------------------------------------------
# 管控/辨识共用详情页 — 子列表展示，点击跳转 method 页
# ------------------------------------------------------------------

async def build_identify_detail_view(page: ft.Page, record_id: str, *, source: str = "identify") -> ft.View:
    """管控清单/辨识清单详情 — 展示风险分析结果列表。

    source: "controls"(from=1) 或 "identify"(from=2)，控制 method 页是否可进入子详情。
    """
    from_val = "1" if source == "controls" else "2"

    async def _on_load(rid: str) -> dict:
        result = await ss.query_identify_by_id(rid)
        if isinstance(result, dict):
            return result
        return {}

    def _build_content(data: dict) -> ft.Control:
        title_text = data.get("title", "风险分析结果")
        method = data.get("method", "")
        data_index = data.get("dataIndex", "")
        items = data.get("list", [])

        if not items:
            return ft.Container(
                content=ft.Text("暂无数据", size=14, color=ft.colors.GREY_400),
                alignment=ft.alignment.center,
                padding=ft.padding.only(top=80),
            )

        rows: list[ft.Control] = []
        for item in items:
            val = str(item.get(data_index, "") or "-")

            def _make_click(item_data):
                async def _click(e):
                    await page.go_async(
                        f"/security/method?id={item_data.get('id', '')}&method={method}&from={from_val}"
                    )
                return _click

            rows.append(
                ft.Container(
                    content=ft.ListTile(
                        title=ft.Text(title_text, size=14),
                        subtitle=ft.Text(val, size=13, color=ft.colors.GREY_600),
                        trailing=ft.Icon(ft.icons.CHEVRON_RIGHT, color=ft.colors.GREY_400),
                    ),
                    on_click=_make_click(item),
                    bgcolor=ft.colors.WHITE,
                    border=ft.border.only(bottom=ft.border.BorderSide(0.5, ft.colors.GREY_200)),
                )
            )

        return ft.Column(controls=[
            ft.Container(
                content=ft.Text("风险分析结果", size=15, weight=ft.FontWeight.W_500),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
            ),
            *rows,
        ], spacing=0)

    from components.detail_page import build_detail_page
    return await build_detail_page(
        page,
        title="风险辨识清单详情",
        record_id=record_id,
        on_load_data=_on_load,
        build_content=_build_content,
    )


# ==================================================================
# 安全管控方法 (method) — 中间页，根据方法类型展示不同列表
# ==================================================================

async def build_method_view(page: ft.Page, record_id: str, method: str, from_val: str) -> ft.View:
    """安全管控方法页 — hazop/jha/lopa/scl 四种展示。"""

    # 方法类型对应的列表字段
    method_fields: dict[str, list[tuple[str, str]]] = {
        "lopa": [("场景", "cj"), ("后果", "hg")],
        "hazop": [("引导词", "ydc"), ("偏差", "pc"), ("后果", "hg")],
        "jha": [("风险源或潜在事件", "eventId_dictText"), ("可能发生的事故类型及后果", "knfsdsglxjhg_dictText")],
        "scl": [("标准", "bzId_dictText"), ("不符合标准情况及后果", "bfhbzqkjhg_dictText")],
    }

    async def _on_load(rid: str) -> dict:
        result = await ss.query_method_data(method, rid)
        if isinstance(result, dict):
            return {"records": result.get("records", [])}
        return {"records": []}

    def _build_content(data: dict) -> ft.Control:
        records = data.get("records", [])
        fields = method_fields.get(method, [])

        if not records:
            return ft.Container(
                content=ft.Text("暂无数据", size=14, color=ft.colors.GREY_400),
                alignment=ft.alignment.center,
                padding=ft.padding.only(top=80),
            )

        cards: list[ft.Control] = []
        for item in records:
            rows = [
                ft.Row(
                    controls=[
                        ft.Text(f"{label}:", size=13, color=ft.colors.GREY_600),
                        ft.Text(str(item.get(key, "") or "-"), size=13, expand=True),
                    ],
                    spacing=6,
                )
                for label, key in fields
            ]

            # from=1(管控)时可点击进入详情, from=2(辨识)不可
            if from_val != "2":
                def _make_click(item_data):
                    async def _click(e):
                        await page.go_async(
                            f"/security/method/detail?method={method}&id={item_data.get('id', '')}"
                        )
                    return _click
                on_click = _make_click(item)
            else:
                on_click = None

            cards.append(
                ft.Container(
                    content=ft.Column(controls=rows, spacing=6),
                    padding=ft.padding.all(14),
                    bgcolor=ft.colors.WHITE,
                    border_radius=8,
                    margin=ft.margin.only(left=12, right=12, top=8),
                    on_click=on_click,
                    ink=on_click is not None,
                )
            )

        return ft.Column(controls=cards, spacing=0)

    from components.detail_page import build_detail_page
    return await build_detail_page(
        page,
        title="风险分析结果",
        record_id=record_id,
        on_load_data=_on_load,
        build_content=_build_content,
    )


# ==================================================================
# 安全管控方法详情 (method detail) — 风险评价 + 控制措施 + 建议措施
# ==================================================================

async def build_method_detail_view(page: ft.Page, record_id: str, method: str) -> ft.View:
    """方法详情页 — 显示风险评价、现有控制措施、建议新增措施。"""

    async def _on_load(rid: str) -> dict:
        result = await ss.query_method_detail(method, rid)
        if isinstance(result, dict):
            records = result.get("records", [])
            return records[0] if records else {}
        return {}

    def _build_content(data: dict) -> ft.Control:
        sections: list[ft.Control] = []

        # 风险评价
        sections.append(detail_section("风险评价", [
            readonly_field("可能性", str(data.get("knx", "") or "-")),
            readonly_field("严重性", str(data.get("yzx", "") or "-")),
            readonly_field("风险值", str(data.get("fxz", "") or "-")),
            readonly_field("评价级别", str(data.get("pjjb", "") or "-")),
            readonly_field("风险级别", str(data.get("fxjb", data.get("fxz", "")) or "-")),
            readonly_field("风险分级", str(data.get("fxfj", "") or "-")),
            readonly_field("管控级别", str(data.get("gkjb", "") or "-")),
        ]))

        # 现有控制措施
        sections.append(detail_section("现有控制措施", [
            readonly_field("工程技术措施", str(data.get("gcjscs", "") or "-")),
            readonly_field("管理措施", str(data.get("glcs", "") or "-")),
            readonly_field("培训教育措施", str(data.get("pxjycs", "") or "-")),
            readonly_field("个体防护措施", str(data.get("gtfhcs", "") or "-")),
            readonly_field("应急处置措施", str(data.get("yjczcs", "") or "-")),
        ]))

        # 建议新增(改进)措施
        sections.append(detail_section("建议新增(改进)措施", [
            readonly_field("", str(data.get("jyxzcs", "") or "无")),
        ]))

        return ft.Column(controls=sections, spacing=0)

    from components.detail_page import build_detail_page
    return await build_detail_page(
        page,
        title="风险分析结果详情",
        record_id=record_id,
        on_load_data=_on_load,
        build_content=_build_content,
    )


# ==================================================================
# 7. 风险点台账 — 多 section 详情
# ==================================================================

build_risk_point_list_view = make_list_view_builder(
    title="风险点台账",
    list_api=ss.risk_point_page_list,
    list_fields=[
        ("风险点编号", "fxdbh"),
        ("风险点名称", "fxdmc"),
        ("所属分区", "ssfq_dictText"),
        ("所属部门", "szbm_dictText"),
        ("风险点分类", "fxdfl_dictText"),
        ("风险等级", "fxdj_dictText"),
        ("责任人", "zrr_dictText"),
    ],
    detail_route="/security/risk_point/detail",
)


async def build_risk_point_detail_view(page: ft.Page, record_id: str) -> ft.View:
    """风险点台账详情 — 基本信息 + 风险分析基本信息 + 风险等级最高级信息"""

    async def _on_load(rid: str) -> dict:
        # 两个 API 并行获取
        import asyncio
        info_task = ss.query_point_by_id(rid)
        max_risk_task = ss.query_max_risk_by_id(rid)
        info_result, max_risk_result = await asyncio.gather(info_task, max_risk_task)

        info = {}
        if isinstance(info_result, dict):
            records = info_result.get("records", [])
            info = records[0] if records else {}

        max_risk = {}
        if isinstance(max_risk_result, dict):
            max_risk = max_risk_result.get("maxRisk", {}) or {}

        return {**info, "_max_risk": max_risk}

    def _build_content(data: dict) -> ft.Control:
        max_risk = data.get("_max_risk", {})

        sections: list[ft.Control] = []

        sections.append(detail_section("基本信息", [
            readonly_field("风险点编号", str(data.get("fxdbh", "") or "-")),
            readonly_field("风险点名称", str(data.get("fxdmc", "") or "-")),
            readonly_field("所属分区", str(data.get("ssfq_dictText", "") or "-")),
            readonly_field("所在部门", str(data.get("szbm_dictText", "") or "-")),
            readonly_field("所属岗位", str(data.get("ssgw_dictText", "") or "-")),
            readonly_field("风险点分类", str(data.get("fxdfl_dictText", "") or "-")),
            readonly_field("关联信息", str(data.get("glxx", "") or "-")),
            readonly_field("风险要素", str(data.get("fxys_dictText", "") or "-")),
            readonly_field("审核人", str(data.get("auditor_dictText", "") or "-")),
            readonly_field("责任人", str(data.get("zrr_dictText", "") or "-")),
            readonly_field("相关附件", str(data.get("xgfj", "") or "-")),
        ]))

        sections.append(detail_section("风险分析基本信息", [
            readonly_field("风险分级方法", str(data.get("fxfjff_dictText", "") or "-")),
            readonly_field("安全警示标示", str(data.get("aqjsbs_dictText", "") or "-")),
            readonly_field("风险分级人员", str(data.get("fxfjry_dictText", "") or "-")),
        ]))

        sections.append(detail_section("风险等级最高级信息", [
            readonly_field("风险级别", str(max_risk.get("fxfj", "") or "-")),
            readonly_field("风险值", str(max_risk.get("fxz", "") or "-")),
            readonly_field("管控级别", str(max_risk.get("gkjb", "") or "-")),
        ]))

        return ft.Column(controls=sections, spacing=0)

    from components.detail_page import build_detail_page
    return await build_detail_page(
        page,
        title="风险点详情",
        record_id=record_id,
        on_load_data=_on_load,
        build_content=_build_content,
    )


# ==================================================================
# 8. 风险分区台账 — 复杂详情（4 个 API）
# ==================================================================

build_risk_area_list_view = make_list_view_builder(
    title="风险分区台账",
    list_api=ss.risk_zoning_page_list,
    list_fields=[
        ("风险分区编号", "fxfqbh"),
        ("风险分区名称", "fxfqmc"),
        ("风险等级", "fxdj_dictText"),
        ("固有风险等级", "gyfxdj_dictText"),
        ("控制风险等级", "kzfxdj_dictText"),
        ("风险校对因素", "fxjzys_dictText"),
        ("责任人", "zrr_dictText"),
    ],
    detail_route="/security/risk_area/detail",
)


async def build_risk_area_detail_view(page: ft.Page, record_id: str) -> ft.View:
    """风险分区台账详情 — 基本信息 + 固有风险等级 + 控制风险等级 + 校正因素 + 评价记录"""

    async def _on_load(rid: str) -> dict:
        import asyncio
        tasks = await asyncio.gather(
            ss.query_zoning_by_id(rid),
            ss.query_records_page_by_id(rid),
            ss.query_risk_level_vo_by_id(rid),
            ss.query_factors_page_by_id(rid),
        )
        info_result, records_result, control_result, factors_result = tasks

        info = {}
        if isinstance(info_result, dict):
            records = info_result.get("records", [])
            info = records[0] if records else {}

        eval_records = []
        if isinstance(records_result, dict):
            eval_records = records_result.get("records", [])

        control = control_result if isinstance(control_result, dict) else {}

        correct = []
        if isinstance(factors_result, dict):
            correct = factors_result.get("records", [])

        return {**info, "_eval_records": eval_records, "_control": control, "_correct": correct}

    def _build_content(data: dict) -> ft.Control:
        control = data.get("_control", {})
        correct = data.get("_correct", [])
        eval_records = data.get("_eval_records", [])

        sections: list[ft.Control] = []

        # 基本信息
        sections.append(detail_section("基本信息", [
            readonly_field("风险分区编号", str(data.get("fxfqbh", "") or "-")),
            readonly_field("风险分区名称", str(data.get("fxfqmc", "") or "-")),
            readonly_field("所在部门", str(data.get("szbm_dictText", "") or "-")),
            readonly_field("责任人", str(data.get("zrr_dictText", "") or "-")),
        ]))

        # 固有风险等级
        lvalue = data.get("lvalue", "")
        svalue = data.get("svalue", "")
        r_value = ""
        if lvalue and svalue:
            try:
                r_value = str(int(lvalue) * int(svalue))
            except (ValueError, TypeError):
                r_value = "-"

        # 固有风险等级章节：含分析方法原则与计算公式（对齐 uniapp）
        principle_text = (
            "分析方法原则：\n"
            "企业根据区域内事故发生的可能性 L 值和事故后果的严重性 S 值，"
            "计算风险 R 值，确定区域固有风险等级\n\n"
            "计算公式：\nR = L * S"
        )
        sections.append(detail_section("固有风险等级", [
            ft.Container(
                content=ft.Text(
                    principle_text,
                    size=13, color=ft.colors.GREY_700, selectable=True,
                ),
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
            ),
            readonly_field("L 值分析 L 值为", str(lvalue or "-")),
            readonly_field("S 值分析 S 值为", str(svalue or "-")),
            readonly_field("R 值为", r_value or "-"),
            readonly_field("固有风险等级", str(data.get("gyfxdj_dictText", "") or "-")),
        ]))

        # 控制风险等级分析
        control_fields = [
            readonly_field("控制风险等级", str(data.get("kzfxdj_dictText", "") or "-")),
            readonly_field("所含风险点", f"{control.get('total', 0)}个"),
            readonly_field("重大风险", str(control.get("count1", 0))),
            readonly_field("较大风险", str(control.get("count2", 0))),
            readonly_field("一般风险", str(control.get("count3", 0))),
            readonly_field("低风险", str(control.get("count4", 0))),
        ]
        sections.append(detail_section("控制风险等级分析", control_fields))

        # 风险校正因素
        if correct:
            factors_text = "\n".join(
                f"{i + 1}.{item.get('correctiveId_dictText', '')}" for i, item in enumerate(correct)
            )
        else:
            factors_text = "无"
        sections.append(detail_section("风险校正因素", [
            readonly_field("", factors_text),
        ]))

        # 评价记录（表格）
        if eval_records:
            table_rows = [
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(r.get("fprq", "") or "-"), size=12)),
                    ft.DataCell(ft.Text(str(r.get("fpr_dictText", "") or "-"), size=12)),
                    ft.DataCell(ft.Text(str(r.get("fxdj_dictText", "") or "-"), size=12)),
                ])
                for r in eval_records
            ]
            table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("评价时间", size=13, weight=ft.FontWeight.W_500)),
                    ft.DataColumn(ft.Text("评价人", size=13, weight=ft.FontWeight.W_500)),
                    ft.DataColumn(ft.Text("评价结果", size=13, weight=ft.FontWeight.W_500)),
                ],
                rows=table_rows,
                border=ft.border.all(0.5, ft.colors.GREY_300),
                horizontal_lines=ft.border.BorderSide(0.5, ft.colors.GREY_200),
            )
            sections.append(detail_section("评价记录", [
                ft.Container(content=table, padding=ft.padding.symmetric(horizontal=8)),
            ]))
        else:
            sections.append(detail_section("评价记录", [
                readonly_field("", "暂无数据"),
            ]))

        return ft.Column(controls=sections, spacing=0)

    from components.detail_page import build_detail_page
    return await build_detail_page(
        page,
        title="风险分区详情",
        record_id=record_id,
        on_load_data=_on_load,
        build_content=_build_content,
    )


# ==================================================================
# 9. 安全管控方法 — 入口（method 不是独立列表，由 controls/identify 跳转）
#    已在上面定义 build_method_view / build_method_detail_view
# ==================================================================
