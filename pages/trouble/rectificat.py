"""隐患整改 — 列表(Tab) + 详情(工作流) + 新增表单 + 整改/验收处理"""

from __future__ import annotations

import flet as ft

from components.scroll_helper import apply_no_bounce

from services import trouble_service as ts
from components.detail_page import build_detail_page, detail_section
from components.form_fields import (
    text_field, dropdown_field, textarea_field, date_field, readonly_field,
    radio_field, form_item,
)
from components.image_upload import ImageUpload
from components.status_badge import status_badge
from utils.app_state import app_state


# ============================================================
# 1. 整改列表页 (Tab: 待处理 / 所有)
# ============================================================

_RECT_TABS = [("待处理", "1"), ("所有", "2")]


async def build_rectificat_view(page: ft.Page, module_type: str = "trouble") -> ft.View:
    """整改台账列表，含 Tab 切换和新增按钮。"""
    is_bbzrz = module_type == "bbzrz"
    title = "包保责任制整改" if is_bbzrz else "隐患整改"

    current_tab = [0]
    current_page = [1]
    page_size = 10
    items_data: list[dict] = []
    is_loading = [False]

    list_column = ft.Column(spacing=0, expand=True)
    loading_ring = ft.ProgressRing(width=24, height=24, visible=False)
    load_more_btn = ft.Container(visible=False)
    empty_widget = ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(ft.icons.INBOX_OUTLINED, size=64, color=ft.colors.GREY_300),
                ft.Text("暂无数据", size=14, color=ft.colors.GREY_400),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8,
        ),
        alignment=ft.alignment.center,
        padding=ft.padding.only(top=120),
        visible=False,
    )

    async def _load_data(reset: bool = False):
        if is_loading[0]:
            return
        is_loading[0] = True
        loading_ring.visible = True
        await page.update_async()

        if reset:
            current_page[0] = 1
            items_data.clear()
            list_column.controls.clear()

        try:
            biz_type = _RECT_TABS[current_tab[0]][1]
            # taskType 区分模块：隐患整改=0，包保责任制整改=1。缺失会导致后端返回数据不符预期。
            result = await ts.get_rect_list({
                "bizTaskType": biz_type,
                "taskType": 1 if is_bbzrz else 0,
                "pageNo": current_page[0],
                "pageSize": page_size,
            })
            records = result.get("records", []) if isinstance(result, dict) else []
            total = result.get("total", 0) if isinstance(result, dict) else 0

            for item in records:
                items_data.append(item)
                ctrl = _build_rect_item(item)

                def _make_click(data):
                    async def _click(e):
                        await page.go_async(
                            f"/{module_type}/rectificat/detail?id={data['id']}"
                        )
                    return _click

                list_column.controls.append(
                    ft.Container(content=ctrl, on_click=_make_click(item), ink=True)
                )

            has_more = len(items_data) < total
            load_more_btn.visible = has_more
            if has_more:
                load_more_btn.content = ft.TextButton(
                    "加载更多", on_click=_on_load_more,
                    style=ft.ButtonStyle(color=ft.colors.BLUE),
                )
            empty_widget.visible = len(items_data) == 0
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"加载失败：{ex}"), open=True)

        is_loading[0] = False
        loading_ring.visible = False
        await page.update_async()

    async def _on_load_more(e):
        current_page[0] += 1
        await _load_data(reset=False)

    def _build_rect_item(item: dict) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row([
                        ft.Text(
                            item.get("zgbt", ""),
                            size=15, weight=ft.FontWeight.W_500,
                            expand=True, max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        status_badge(item.get("yhjb_dictText", "")),
                    ]),
                    ft.Text(f"整改单号：{item.get('zgdbh', '-')}", size=13, color=ft.colors.GREY_600),
                    ft.Row([
                        ft.Text(f"整改来源：{item.get('zgly_dictText', '-')}", size=12, color=ft.colors.GREY_500, expand=True),
                    ]),
                ],
                spacing=4,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200)),
        )

    # Tab
    async def _on_tab_change(e):
        current_tab[0] = e.control.selected_index
        await _load_data(reset=True)

    tabs = ft.Tabs(
        selected_index=0,
        on_change=_on_tab_change,
        tabs=[ft.Tab(text=label) for label, _ in _RECT_TABS],
        label_color=ft.colors.BLUE,
        unselected_label_color=ft.colors.GREY_600,
        indicator_color=ft.colors.BLUE,
        divider_color=ft.colors.GREY_200,
    )

    # 新增按钮
    async def _on_add(e):
        await page.go_async(f"/{module_type}/rectificat/add")

    fab = ft.FloatingActionButton(
        icon=ft.icons.ADD, on_click=_on_add, bgcolor=ft.colors.BLUE
    )

    scroll_content = ft.ListView(
        controls=[
            list_column,
            ft.Container(
                content=ft.Row([loading_ring], alignment=ft.MainAxisAlignment.CENTER),
                padding=10,
            ),
            load_more_btn,
            empty_widget,
        ],
        expand=True,
    )
    apply_no_bounce(scroll_content)

    body = ft.Column(controls=[tabs, scroll_content], spacing=0, expand=True)

    view = ft.View(
        route=f"/{module_type}/rectificat",
        appbar=ft.AppBar(title=ft.Text(title), bgcolor=ft.colors.WHITE),
        controls=[body],
        floating_action_button=fab,
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    await _load_data(reset=True)
    return view


# ============================================================
# 2. 整改详情页（含工作流步骤 + 操作按钮）
# ============================================================

_STEPS = ["整改通知", "隐患整改", "问题验证"]


async def build_rectificat_detail_view(
    page: ft.Page, record_id: str, module_type: str = "trouble"
) -> ft.View:
    """整改详情：显示三阶段信息 + 根据状态显示操作按钮。
    先返回带 loading 的 View，数据异步加载后渲染，避免阻塞 UI。"""
    import asyncio

    title = "整改详情"

    # --- UI 骨架 ---
    loading = ft.Container(
        content=ft.ProgressRing(width=32, height=32),
        alignment=ft.alignment.center,
        expand=True,
    )
    error_widget = ft.Container(visible=False, expand=True)
    content_area = ft.Container(expand=True)
    bottom_bar = ft.Container(visible=False)

    body = ft.Column(
        controls=[loading, error_widget, content_area, bottom_bar],
        spacing=0,
        expand=True,
    )

    view = ft.View(
        route=f"/{module_type}/rectificat/detail",
        appbar=ft.AppBar(title=ft.Text(title), bgcolor=ft.colors.WHITE),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    # --- 异步加载数据 + 渲染 ---
    async def _load_and_render():
        try:
            # 1. 加载详情
            data = await ts.get_rect_detail(record_id)
            rec_status = str(data.get("recStatus", ""))

            # 2. 并行检查权限（仅在需要时）
            can_zg = False
            can_ys = False
            if rec_status == "3":
                try:
                    can_zg = bool(await ts.check_zgr({"id": record_id}))
                except Exception:
                    pass
            elif rec_status == "4":
                try:
                    can_ys = bool(await ts.check_ysr({"id": record_id}))
                except Exception:
                    pass

            # 3. 构建内容
            content_ctrl = _build_content(data)
            content_area.content = ft.ListView(
                controls=[content_ctrl],
                expand=True,
                padding=0,
            )

            # 4. 构建操作按钮
            async def _go_zg_deal(e):
                await page.go_async(f"/{module_type}/rectificat/deal_zg?id={record_id}")

            async def _go_ys_deal(e):
                await page.go_async(f"/{module_type}/rectificat/deal_ys?id={record_id}")

            btn_controls: list[ft.Control] = []
            if can_zg:
                btn_controls.append(ft.ElevatedButton(
                    "整改处理", on_click=_go_zg_deal,
                    bgcolor=ft.colors.BLUE, color=ft.colors.WHITE, expand=True,
                ))
            if can_ys:
                btn_controls.append(ft.ElevatedButton(
                    "验收处理", on_click=_go_ys_deal,
                    bgcolor=ft.colors.BLUE, color=ft.colors.WHITE, expand=True,
                ))
            if btn_controls:
                bottom_bar.content = ft.Row(controls=btn_controls, spacing=12)
                bottom_bar.padding = ft.padding.symmetric(horizontal=16, vertical=10)
                bottom_bar.bgcolor = ft.colors.WHITE
                bottom_bar.border = ft.border.only(top=ft.border.BorderSide(1, ft.colors.GREY_200))
                bottom_bar.visible = True

            loading.visible = False

        except Exception as ex:
            loading.visible = False
            error_widget.visible = True
            error_widget.content = ft.Column(
                controls=[
                    ft.Icon(ft.icons.ERROR_OUTLINE, size=48, color=ft.colors.RED_300),
                    ft.Text(f"加载失败：{ex}", size=14, color=ft.colors.GREY_600),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
            )
            error_widget.alignment = ft.alignment.center

        await page.update_async()

    def _build_content(d: dict) -> ft.Control:
        rec_status = str(d.get("recStatus", ""))

        # 工作流步骤指示器
        step_index = 0
        if rec_status in ("3",):
            step_index = 1
        elif rec_status in ("4",):
            step_index = 2
        elif rec_status in ("5", "6"):
            step_index = 3

        step_row = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            width=28, height=28,
                            border_radius=14,
                            bgcolor=ft.colors.BLUE if i <= step_index else ft.colors.GREY_300,
                            alignment=ft.alignment.center,
                            content=ft.Text(str(i + 1), size=13, color=ft.colors.WHITE),
                        ),
                        ft.Text(_STEPS[i], size=11,
                                color=ft.colors.BLUE if i <= step_index else ft.colors.GREY_500),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                    expand=True,
                )
                for i in range(len(_STEPS))
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        )
        step_card = ft.Container(
            content=step_row,
            bgcolor=ft.colors.WHITE,
            padding=ft.padding.symmetric(horizontal=8, vertical=12),
            margin=ft.margin.only(bottom=10),
        )

        # 整改通知单
        notice_section = detail_section("整改通知单", [
            readonly_field("整改单号", d.get("zgdbh", "")),
            readonly_field("整改标题", d.get("zgbt", "")),
            readonly_field("风险分析对象", d.get("riskAnalysisObjectId_dictText", "")),
            readonly_field("管控措施", d.get("riskManageMeasureId_dictText", "")),
            readonly_field("隐患级别", d.get("yhjb_dictText", "")),
            readonly_field("登记时间", d.get("djsj", "")),
            readonly_field("发现人", d.get("fxr_dictText", "")),
            readonly_field("检查来源", d.get("jclyfl_dictText", "")),
            readonly_field("治理类型", d.get("zllx_dictText", "")),
            readonly_field("隐患分类", d.get("zyfl_dictText", "")),
            readonly_field("隐患描述", d.get("yhms", "")),
            readonly_field("整改责任人", d.get("zrr_dictText", "")),
            readonly_field("要求整改完成日期", d.get("yqzgwcrq", "")),
            readonly_field("备注", d.get("bz", "")),
        ])

        # 整改照片
        photos_scxg = d.get("scxgzp", "")
        photo_section_1 = ft.Container()
        if photos_scxg:
            photo_section_1 = ft.Container(
                content=ImageUpload(
                    page, disabled=True,
                    initial_images=[p for p in photos_scxg.split(",") if p],
                ),
                padding=ft.padding.symmetric(horizontal=16),
                bgcolor=ft.colors.WHITE,
                margin=ft.margin.only(bottom=10),
            )

        # 整改报告
        report_section = detail_section("隐患整改报告", [
            readonly_field("整改完成日期", d.get("zgwcrq", "")),
            readonly_field("治理资金", d.get("zlzj", "")),
            readonly_field("整改人", d.get("zrr_dictText", "")),
            readonly_field("填报日期", d.get("tbrq", "")),
            readonly_field("整改情况", d.get("zgqk", "")),
            readonly_field("原因分析", d.get("yyfx", "")),
        ])

        # 整改照片
        photos_zg = d.get("zgxgzp", "")
        photo_section_2 = ft.Container()
        if photos_zg:
            photo_section_2 = ft.Container(
                content=ImageUpload(
                    page, disabled=True,
                    initial_images=[p for p in photos_zg.split(",") if p],
                ),
                padding=ft.padding.symmetric(horizontal=16),
                bgcolor=ft.colors.WHITE,
                margin=ft.margin.only(bottom=10),
            )

        # 验收信息
        verify_section = detail_section("问题验证", [
            readonly_field("验收人", d.get("ysr_dictText", "")),
            readonly_field("确认日期", d.get("qrrq", "")),
            readonly_field("确认结果", d.get("qrjg_dictText", "")),
        ])

        return ft.Column(
            controls=[
                step_card, notice_section, photo_section_1,
                report_section, photo_section_2, verify_section,
            ],
            spacing=0,
        )

    asyncio.ensure_future(_load_and_render())
    return view


# ============================================================
# 3. 新增整改表单
# ============================================================

async def build_rectificat_add_view(
    page: ft.Page, module_type: str = "trouble"
) -> ft.View:
    """新增隐患整改表单页。"""
    is_bbzrz = module_type == "bbzrz"
    title = "新增包保责任制整改" if is_bbzrz else "新增隐患整改"

    # 表单数据；taskType 区分模块，后端需要此字段区分普通隐患/包保
    form = {
        "zgbt": "", "riskAnalysisObjectId": "", "riskManageMeasureId": "",
        "yhjb": "", "djsj": "", "fxr": "", "jclyfl": "",
        "zllx": "", "zyfl": "", "yhms": "", "zrr": "",
        "yqzgwcrq": "", "bz": "",
        "taskType": 1 if is_bbzrz else 0,
    }

    # 字典选项
    risk_objects: list[dict] = []
    risk_measures: list[dict] = []
    yhjb_options: list[dict] = []
    jclyfl_options: list[dict] = []
    zllx_options: list[dict] = []
    zyfl_options: list[dict] = []
    people_list: list[dict] = []

    # 图片上传组件引用
    image_upload = ImageUpload(page, max_count=9)

    # 加载字典和下拉选项
    async def _load_options():
        nonlocal risk_objects, risk_measures, yhjb_options, jclyfl_options
        nonlocal zllx_options, zyfl_options, people_list

        try:
            # 并行加载字典
            import asyncio
            results = await asyncio.gather(
                ts.get_risk_object_list({"pageNo": 1, "pageSize": 200}),
                ts.get_dict_items("hidden_danger_level"),
                ts.get_dict_items("jclyfl"),
                ts.get_dict_items("zllx"),
                ts.get_dict_items("zyfl"),
                ts.get_people_list({"pageNo": 1, "pageSize": 200}),
                return_exceptions=True,
            )

            # 风险对象
            if isinstance(results[0], dict):
                for r in results[0].get("records", []):
                    risk_objects.append({
                        "text": r.get("riskAnalysisObjectName", ""),
                        "value": r.get("id", ""),
                    })

            # 字典项解析辅助
            def _parse_dict(res):
                if isinstance(res, list):
                    return [{"text": it.get("text", ""), "value": str(it.get("value", ""))} for it in res]
                return []

            yhjb_options.extend(_parse_dict(results[1]))
            jclyfl_options.extend(_parse_dict(results[2]))
            zllx_options.extend(_parse_dict(results[3]))
            zyfl_options.extend(_parse_dict(results[4]))

            # 人员
            if isinstance(results[5], dict):
                for u in results[5].get("records", results[5].get("list", [])):
                    people_list.append({
                        "text": u.get("realname", u.get("username", "")),
                        "value": u.get("username", u.get("id", "")),
                    })
        except Exception:
            pass

    await _load_options()

    # 风险对象变更时联动加载措施
    async def _on_object_change(e):
        form["riskAnalysisObjectId"] = e.control.value or ""
        risk_measures.clear()
        if form["riskAnalysisObjectId"]:
            try:
                res = await ts.get_risk_measure_by_object(form["riskAnalysisObjectId"])
                if isinstance(res, list):
                    for m in res:
                        risk_measures.append({
                            "text": m.get("manageMeasureDesc", ""),
                            "value": m.get("id", ""),
                        })
                elif isinstance(res, dict):
                    for m in res.get("records", []):
                        risk_measures.append({
                            "text": m.get("manageMeasureDesc", ""),
                            "value": m.get("id", ""),
                        })
            except Exception:
                pass
        # 刷新措施下拉
        measure_dd.options = [ft.dropdown.Option(key=o["value"], text=o["text"]) for o in risk_measures]
        measure_dd.value = None
        await page.update_async()

    def _set(key):
        def _on_change(e):
            form[key] = e.control.value or ""
        return _on_change

    # 日期选择器辅助
    async def _pick_date(field_key, display_tf):
        async def _on_click(e):
            async def _on_date(ev):
                if ev.control.value:
                    val = ev.control.value.strftime("%Y-%m-%d")
                    form[field_key] = val
                    display_tf.value = val
                    await page.update_async()

            dp = ft.DatePicker(on_change=_on_date)
            page.overlay.append(dp)
            await page.update_async()
            dp.pick_date()

        return _on_click

    # --- 构建表单控件 ---
    zgbt_field = text_field("整改标题", on_change=_set("zgbt"), required=True)

    object_dd = ft.Dropdown(
        hint_text="请选择风险分析对象",
        options=[ft.dropdown.Option(key=o["value"], text=o["text"]) for o in risk_objects],
        on_change=_on_object_change,
        border_color=ft.colors.GREY_300,
        text_size=14,
    )
    object_field = form_item("风险对象", object_dd)

    measure_dd = ft.Dropdown(
        hint_text="请选择管控措施",
        options=[ft.dropdown.Option(key=o["value"], text=o["text"]) for o in risk_measures],
        on_change=_set("riskManageMeasureId"),
        border_color=ft.colors.GREY_300,
        text_size=14,
    )
    measure_field = form_item("管控措施", measure_dd)

    yhjb_field = dropdown_field("隐患级别", options=yhjb_options, on_change=_set("yhjb"))
    jclyfl_field = dropdown_field("检查来源", options=jclyfl_options, on_change=_set("jclyfl"))
    zllx_field = dropdown_field("治理类型", options=zllx_options, on_change=_set("zllx"))
    zyfl_field = dropdown_field("隐患分类", options=zyfl_options, on_change=_set("zyfl"))
    yhms_field = textarea_field("隐患描述", on_change=_set("yhms"))

    zrr_field = dropdown_field("整改责任人", options=people_list, on_change=_set("zrr"), required=True)

    # 日期字段（登记时间 / 要求整改完成日期）
    djsj_tf = ft.TextField(
        hint_text="请选择日期", read_only=True,
        border_color=ft.colors.GREY_300, text_size=14,
        suffix_icon=ft.icons.CALENDAR_TODAY,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
    )
    djsj_tf.on_click = await _pick_date("djsj", djsj_tf)
    djsj_field = form_item("登记时间", djsj_tf)

    yqzg_tf = ft.TextField(
        hint_text="请选择日期", read_only=True,
        border_color=ft.colors.GREY_300, text_size=14,
        suffix_icon=ft.icons.CALENDAR_TODAY,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
    )
    yqzg_tf.on_click = await _pick_date("yqzgwcrq", yqzg_tf)
    yqzg_field = form_item("要求完成日期", yqzg_tf, required=True)

    fxr_field = dropdown_field("发现人", options=people_list, on_change=_set("fxr"))
    bz_field = textarea_field("备注", on_change=_set("bz"), rows=2)

    photo_field = form_item("现场照片", image_upload)

    # --- 提交 ---
    async def _on_submit(e):
        if not form["zgbt"]:
            page.snack_bar = ft.SnackBar(ft.Text("请填写整改标题"), open=True)
            await page.update_async()
            return
        if not form["zrr"]:
            page.snack_bar = ft.SnackBar(ft.Text("请选择整改责任人"), open=True)
            await page.update_async()
            return

        submit_data = {**form}
        # 附加图片路径
        paths = image_upload.uploaded_paths
        if paths:
            submit_data["scxgzp"] = ",".join(paths)

        try:
            await ts.add_rect(submit_data)
            page.snack_bar = ft.SnackBar(ft.Text("提交成功"), open=True)
            await page.update_async()
            page.views.pop()
            await page.update_async()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"提交失败：{ex}"), open=True)
            await page.update_async()

    submit_btn = ft.Container(
        content=ft.Row(
            controls=[
                ft.ElevatedButton(
                    "提交", on_click=_on_submit,
                    bgcolor=ft.colors.BLUE, color=ft.colors.WHITE, expand=True,
                ),
            ],
            spacing=12,
        ),
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        bgcolor=ft.colors.WHITE,
        border=ft.border.only(top=ft.border.BorderSide(1, ft.colors.GREY_200)),
    )

    form_column = ft.ListView(
        controls=[
            zgbt_field, object_field, measure_field, yhjb_field,
            djsj_field, fxr_field, jclyfl_field, zllx_field, zyfl_field,
            yhms_field, zrr_field, yqzg_field, photo_field, bz_field,
        ],
        expand=True,
        padding=0,
    )

    body = ft.Column(controls=[form_column, submit_btn], spacing=0, expand=True)

    return ft.View(
        route=f"/{module_type}/rectificat/add",
        appbar=ft.AppBar(title=ft.Text(title), bgcolor=ft.colors.WHITE),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )


# ============================================================
# 4. 整改处理页
# ============================================================

async def build_zg_deal_view(
    page: ft.Page, record_id: str, module_type: str = "trouble"
) -> ft.View:
    """整改处理：填写整改结果并提交。"""
    title = "整改处理"

    form = {
        "id": record_id,
        "zgwcrq": "", "zlzj": "", "zgqk": "", "yyfx": "",
    }

    image_upload = ImageUpload(page, max_count=9)

    def _set(key):
        def _on_change(e):
            form[key] = e.control.value or ""
        return _on_change

    zgwcrq_tf = ft.TextField(
        hint_text="请选择日期", read_only=True,
        border_color=ft.colors.GREY_300, text_size=14,
        suffix_icon=ft.icons.CALENDAR_TODAY,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
    )

    async def _pick_zgwcrq(e):
        async def _on_date(ev):
            if ev.control.value:
                val = ev.control.value.strftime("%Y-%m-%d")
                form["zgwcrq"] = val
                zgwcrq_tf.value = val
                await page.update_async()
        dp = ft.DatePicker(on_change=_on_date)
        page.overlay.append(dp)
        await page.update_async()
        dp.pick_date()

    zgwcrq_tf.on_click = _pick_zgwcrq

    zgwcrq_field = form_item("整改完成日期", zgwcrq_tf, required=True)
    zlzj_field = text_field("治理资金", on_change=_set("zlzj"))
    zgqk_field = textarea_field("整改情况", on_change=_set("zgqk"), required=True)
    yyfx_field = textarea_field("原因分析", on_change=_set("yyfx"))
    photo_field = form_item("整改照片", image_upload)

    async def _on_submit(e):
        if not form["zgwcrq"]:
            page.snack_bar = ft.SnackBar(ft.Text("请选择整改完成日期"), open=True)
            await page.update_async()
            return
        if not form["zgqk"]:
            page.snack_bar = ft.SnackBar(ft.Text("请填写整改情况"), open=True)
            await page.update_async()
            return

        submit_data = {**form}
        paths = image_upload.uploaded_paths
        if paths:
            submit_data["zgxgzp"] = ",".join(paths)

        try:
            await ts.rect_danger(submit_data)
            page.snack_bar = ft.SnackBar(ft.Text("提交成功"), open=True)
            await page.update_async()
            page.views.pop()
            await page.update_async()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"提交失败：{ex}"), open=True)
            await page.update_async()

    submit_btn = ft.Container(
        content=ft.Row([
            ft.ElevatedButton(
                "提交整改", on_click=_on_submit,
                bgcolor=ft.colors.BLUE, color=ft.colors.WHITE, expand=True,
            ),
        ]),
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        bgcolor=ft.colors.WHITE,
        border=ft.border.only(top=ft.border.BorderSide(1, ft.colors.GREY_200)),
    )

    form_column = ft.ListView(
        controls=[zgwcrq_field, zlzj_field, zgqk_field, yyfx_field, photo_field],
        expand=True,
    )

    return ft.View(
        route=f"/{module_type}/rectificat/deal_zg",
        appbar=ft.AppBar(title=ft.Text(title), bgcolor=ft.colors.WHITE),
        controls=[ft.Column([form_column, submit_btn], spacing=0, expand=True)],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )


# ============================================================
# 5. 验收处理页
# ============================================================

async def build_ys_deal_view(
    page: ft.Page, record_id: str, module_type: str = "trouble"
) -> ft.View:
    """验收处理：填写验收结果并提交。"""
    title = "验收处理"

    form = {"id": record_id, "qrrq": "", "qrjg": "", "qrqk": ""}

    def _set(key):
        def _on_change(e):
            form[key] = e.control.value or ""
        return _on_change

    qrrq_tf = ft.TextField(
        hint_text="请选择日期", read_only=True,
        border_color=ft.colors.GREY_300, text_size=14,
        suffix_icon=ft.icons.CALENDAR_TODAY,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
    )

    async def _pick_qrrq(e):
        async def _on_date(ev):
            if ev.control.value:
                val = ev.control.value.strftime("%Y-%m-%d")
                form["qrrq"] = val
                qrrq_tf.value = val
                await page.update_async()
        dp = ft.DatePicker(on_change=_on_date)
        page.overlay.append(dp)
        await page.update_async()
        dp.pick_date()

    qrrq_tf.on_click = _pick_qrrq
    qrrq_field = form_item("确认日期", qrrq_tf, required=True)

    qrjg_field = radio_field(
        "确认结果",
        options=[{"text": "合格", "value": "1"}, {"text": "不合格", "value": "2"}],
        on_change=_set("qrjg"),
        required=True,
    )
    qrqk_field = textarea_field("确认情况", on_change=_set("qrqk"))

    async def _on_submit(e):
        if not form["qrrq"]:
            page.snack_bar = ft.SnackBar(ft.Text("请选择确认日期"), open=True)
            await page.update_async()
            return
        if not form["qrjg"]:
            page.snack_bar = ft.SnackBar(ft.Text("请选择确认结果"), open=True)
            await page.update_async()
            return

        try:
            await ts.yan_shou_danger(form)
            page.snack_bar = ft.SnackBar(ft.Text("提交成功"), open=True)
            await page.update_async()
            page.views.pop()
            await page.update_async()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"提交失败：{ex}"), open=True)
            await page.update_async()

    submit_btn = ft.Container(
        content=ft.Row([
            ft.ElevatedButton(
                "提交验收", on_click=_on_submit,
                bgcolor=ft.colors.BLUE, color=ft.colors.WHITE, expand=True,
            ),
        ]),
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        bgcolor=ft.colors.WHITE,
        border=ft.border.only(top=ft.border.BorderSide(1, ft.colors.GREY_200)),
    )

    form_column = ft.ListView(
        controls=[qrrq_field, qrjg_field, qrqk_field],
        expand=True,
    )

    return ft.View(
        route=f"/{module_type}/rectificat/deal_ys",
        appbar=ft.AppBar(title=ft.Text(title), bgcolor=ft.colors.WHITE),
        controls=[ft.Column([form_column, submit_btn], spacing=0, expand=True)],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )
