"""作业票详情页 — 6 宫格 + 步骤进度 + 摄像头列表（通用，所有类型共用）"""

from __future__ import annotations

from typing import Any

import flet as ft

from pages.ticket.config import (
    DETAIL_STEPS, TICKET_TYPES, get_config_by_type_value,
    get_all_fields, get_detail_display_fields,
)
from services import ticket_service as svc
from utils.app_state import app_state
from components.form_fields import readonly_field


# 步骤图标映射
_STEP_ICONS = {
    "info": ft.icons.INFO_OUTLINE,
    "detection": ft.icons.SCIENCE_OUTLINED,
    "assessment": ft.icons.SECURITY_OUTLINED,
    "clarification": ft.icons.RECORD_VOICE_OVER_OUTLINED,
    "approval": ft.icons.APPROVAL_OUTLINED,
    "acceptance": ft.icons.CHECK_CIRCLE_OUTLINE,
}


async def build_ticket_detail_page(
    page: ft.Page,
    ticket_id: str,
    type_value: str,
) -> ft.View:
    """构建作业票详情页。

    参数:
        ticket_id: 作业票 ID
        type_value: 后端类型值
    """
    config = get_config_by_type_value(type_value)
    if not config:
        return ft.View(route="/ticket/detail", controls=[ft.Text("未知类型")])

    # --- 状态 ---
    base_info: dict[str, Any] = {}
    current_step = [0]
    camera_list: list[dict] = []

    # --- 控件 ---
    step_indicator = ft.Row(spacing=4, alignment=ft.MainAxisAlignment.CENTER)
    grid_container = ft.Column(spacing=0)
    camera_column = ft.Column(spacing=4)
    popup_content = ft.Container(expand=True)
    popup_visible = [False]

    # --- 加载详情 ---
    async def _load_detail():
        nonlocal base_info, camera_list
        try:
            result = await svc.ticket_detail(config.query_path, ticket_id)
            records = result.get("records", []) if isinstance(result, dict) else []
            if records:
                base_info = records[0]
                step_val = base_info.get("step", 1)
                current_step[0] = int(step_val) - 1 if step_val else 0
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"加载失败：{ex}"), open=True)
            await page.update_async()
            return

        # 加载摄像头
        try:
            cam_result = await svc.get_camera_url(config.api_prefix, {
                "id": ticket_id, "zylb": type_value,
            })
            if isinstance(cam_result, list):
                camera_list = cam_result
        except Exception:
            pass

        _build_step_indicator()
        _build_grid()
        _build_camera_list()
        await page.update_async()

    # --- 步骤指示器 ---
    def _build_step_indicator():
        step_indicator.controls.clear()
        for i, s in enumerate(DETAIL_STEPS):
            is_done = i <= current_step[0]
            color = ft.colors.BLUE if is_done else ft.colors.GREY_400
            label = s["label"]
            if i == 1 and config.analysis_title:
                label = config.analysis_title

            step_indicator.controls.append(
                ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Text(str(i + 1), size=12, color=ft.colors.WHITE, text_align=ft.TextAlign.CENTER),
                            width=28, height=28,
                            border_radius=14,
                            bgcolor=color,
                            alignment=ft.alignment.center,
                        ),
                        ft.Text(label, size=10, color=color, text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                    expand=True,
                )
            )

    # --- 6 宫格 ---
    def _build_grid():
        grid_container.controls.clear()
        icons = list(_STEP_ICONS.values())
        rows = []
        for row_start in (0, 3):
            row_items = []
            for i in range(row_start, min(row_start + 3, 6)):
                s = DETAIL_STEPS[i]
                label = s["label"]
                if i == 1 and config.analysis_title:
                    label = config.analysis_title

                def _make_click(idx):
                    async def _click(e):
                        # 不能跳到未到达的步骤
                        if idx - 1 > current_step[0] and idx > 1:
                            page.snack_bar = ft.SnackBar(ft.Text("请先完成前序步骤"), open=True)
                            await page.update_async()
                            return
                        await _show_section(idx)
                    return _click

                row_items.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(icons[i], size=32, color=ft.colors.BLUE),
                                ft.Text(label, size=12, text_align=ft.TextAlign.CENTER),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=4,
                        ),
                        expand=True,
                        on_click=_make_click(i),
                        ink=True,
                        padding=ft.padding.symmetric(vertical=12),
                        alignment=ft.alignment.center,
                    )
                )
            rows.append(ft.Row(controls=row_items))

        grid_container.controls = [
            ft.Container(
                content=ft.Column(rows, spacing=0),
                bgcolor=ft.colors.WHITE,
                border_radius=8,
                margin=ft.margin.symmetric(horizontal=12),
                padding=ft.padding.symmetric(vertical=8),
            )
        ]

    # --- 摄像头列表 ---
    def _build_camera_list():
        camera_column.controls.clear()
        if not camera_list:
            camera_column.controls.append(
                ft.Container(
                    content=ft.Text("未配置摄像头", size=13, color=ft.colors.GREY_500),
                    padding=ft.padding.all(12),
                    bgcolor=ft.colors.WHITE,
                    border_radius=8,
                    margin=ft.margin.symmetric(horizontal=12),
                )
            )
            return

        for cam in camera_list:
            camera_column.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(f"相机编码: {cam.get('cameraCode', '')}", size=12),
                                    ft.Text(f"安装位置: {cam.get('location', '')}", size=12, color=ft.colors.GREY_600),
                                ],
                                expand=True,
                                spacing=4,
                            ),
                            ft.IconButton(ft.icons.PLAY_CIRCLE_OUTLINE, icon_color=ft.colors.BLUE),
                        ],
                    ),
                    padding=ft.padding.all(12),
                    bgcolor=ft.colors.WHITE,
                    border_radius=8,
                    margin=ft.margin.symmetric(horizontal=12, vertical=2),
                )
            )

    # --- 显示各步骤弹出层 ---
    async def _show_section(index: int):
        """根据步骤 index 显示不同的弹出内容"""
        if index == 0:
            content = _build_info_section()
        elif index == 1:
            content = await _build_detection_section()
        elif index == 2:
            content = await _build_assessment_section()
        elif index == 3:
            content = await _build_clarification_section()
        elif index == 4:
            content = await _build_approval_section()
        elif index == 5:
            content = await _build_acceptance_section()
        else:
            content = ft.Text("未知步骤")

        # 弹出层
        bs = ft.BottomSheet(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(
                                    DETAIL_STEPS[index]["label"] if index != 1 else config.analysis_title,
                                    size=16, weight=ft.FontWeight.BOLD,
                                ),
                                ft.IconButton(
                                    ft.icons.CLOSE,
                                    on_click=lambda e: _close_bs(bs),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Divider(height=1),
                        ft.Container(content=content, expand=True),
                    ],
                    expand=True,
                ),
                padding=16,
                height=page.height * 0.84 if page.height else 600,
            ),
            open=True,
        )
        page.overlay.append(bs)
        await page.update_async()

    def _close_bs(bs):
        bs.open = False
        page.update()

    # --- 基本信息 ---
    def _build_info_section() -> ft.Control:
        """渲染基本信息（只读展示所有字段）"""
        all_f = get_detail_display_fields(config)
        rows = []
        for f in all_f:
            val = base_info.get(f"{f.key}_dictText") or base_info.get(f.key, "")
            rows.append(readonly_field(f.label, str(val) if val else ""))

        return ft.ListView(controls=rows, expand=True, spacing=0)

    # --- 安全分析 ---
    async def _show_detection_detail(insp: dict):
        """动火分析项详情弹框（只读）。"""
        sign_path = insp.get("signArea", "")
        sign_widget: ft.Control
        if sign_path:
            sign_src = (
                sign_path if sign_path.startswith("http")
                else f"{app_state.host}/jeecg-boot/sys/common/static/{sign_path}"
            )
            sign_widget = ft.Image(src=sign_src, height=80, fit=ft.ImageFit.CONTAIN)
        else:
            sign_widget = ft.Text("未签名", size=12, color=ft.colors.GREY_500)

        dlg = ft.AlertDialog(
            title=ft.Text(f"分析点：{insp.get('fxdmc', '')}"),
            content=ft.Container(
                width=320,
                content=ft.Column(
                    controls=[
                        readonly_field("分析人", str(insp.get("fxrName", "") or "-")),
                        readonly_field("代表性气体", str(insp.get("dbxqt", "") or "-")),
                        readonly_field("分析结果 / %", str(insp.get("fxjg", "") or "-")),
                        readonly_field("结果备注", str(insp.get("remark", "") or "-")),
                        readonly_field("提交时间", str(insp.get("submitTime", "") or "-")),
                        ft.Text("分析人签字", size=13, weight=ft.FontWeight.W_500),
                        sign_widget,
                    ],
                    tight=True, spacing=6,
                ),
            ),
            actions=[ft.TextButton("关闭", on_click=lambda e: _close_dialog(dlg))],
        )
        page.dialog = dlg
        dlg.open = True
        await page.update_async()

    def _close_dialog(dlg):
        dlg.open = False
        page.update()

    async def _build_detection_section() -> ft.Control:
        """安全分析步骤"""
        permissions = False
        try:
            inspections = await svc.get_inspection_by_id(config.api_prefix, ticket_id)
            # API 返回 {data: [...], permissions: bool}
            if isinstance(inspections, dict):
                items = inspections.get("data", []) or []
                permissions = inspections.get("permissions", False)
            elif isinstance(inspections, list):
                items = inspections
            else:
                items = []
        except Exception:
            items = []

        # 检查是否需要分析
        need_analysis = str(base_info.get("sfxyaqjc", "1")) == "1"
        if not need_analysis:
            return ft.Text("不需要进行分析!", color=ft.colors.GREY_500)

        if not items:
            rows: list[ft.Control] = [ft.Text("暂无分析数据", color=ft.colors.GREY_500)]
        else:
            rows = []
            for insp in items:
                def _make_detection_click(data):
                    async def _click(e):
                        await _show_detection_detail(data)
                    return _click

                rows.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"分析点: {insp.get('fxdmc', '')}", size=13, weight=ft.FontWeight.W_500),
                            ft.Text(f"分析人: {insp.get('fxrName', '')}", size=12, color=ft.colors.GREY_600),
                            ft.Text(f"代表性气体: {insp.get('dbxqt', '')}", size=12, color=ft.colors.GREY_600),
                            ft.Text(f"分析结果: {insp.get('fxjg', '')}", size=12, color=ft.colors.GREY_600),
                            ft.Text(f"提交时间: {insp.get('submitTime', '')}", size=12, color=ft.colors.GREY_600),
                        ], spacing=4),
                        padding=12,
                        bgcolor=ft.colors.GREY_50,
                        border_radius=8,
                        margin=ft.margin.only(bottom=8),
                        on_click=_make_detection_click(insp),
                        ink=True,
                    )
                )

        disabled = current_step[0] >= 1

        async def _submit_detection(e):
            try:
                await svc.submit_inspection(config.api_prefix, ticket_id)
                page.snack_bar = ft.SnackBar(ft.Text("提交成功"), open=True)
                await _load_detail()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"失败：{ex}"), open=True)
                await page.update_async()

        if permissions and not disabled and items:
            rows.append(
                ft.ElevatedButton(
                    "提交分析结果",
                    on_click=_submit_detection,
                    bgcolor=ft.colors.BLUE,
                    color=ft.colors.WHITE,
                )
            )

        return ft.ListView(controls=rows, expand=True)

    # --- 安全评估 ---
    async def _build_assessment_section() -> ft.Control:
        """安全评估 — 危害辨识 + 安全措施"""
        permissions = False
        measure_step = 0

        # 危害辨识
        try:
            harm_list = await svc.get_dict_harm(config.api_prefix, ticket_id)
            if not isinstance(harm_list, list):
                harm_list = []
        except Exception:
            harm_list = []

        # 安全措施 — API 返回 {data: [...], permissions, step, zyrPermissions, ...}
        try:
            measures = await svc.get_measure_by_id(config.api_prefix, ticket_id)
            if isinstance(measures, dict):
                measure_items = measures.get("data", []) or []
                permissions = measures.get("permissions", False)
                measure_step = measures.get("step", 0)
            elif isinstance(measures, list):
                measure_items = measures
            else:
                measure_items = []
        except Exception:
            measure_items = []

        disabled = current_step[0] >= 2

        # 危害辨识显示
        whbs_text = base_info.get("whbs_dictText", "")
        rows: list[ft.Control] = [
            ft.Text("危害辨识", size=14, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Text(whbs_text or "暂无", size=12, color=ft.colors.GREY_600),
                padding=12,
                bgcolor=ft.colors.GREY_50,
                border_radius=8,
                margin=ft.margin.only(bottom=8),
            ),
            ft.Text("安全措施", size=14, weight=ft.FontWeight.BOLD),
        ]

        for m in measure_items:
            sign_area = m.get("signArea", "")
            selected = m.get("selected", "")
            # 有签名或有选择状态表示已确认
            if sign_area:
                status_text = "涉及" if str(selected) == "1" else ("不涉及" if str(selected) == "2" else "已确认")
                status_color = ft.colors.GREEN
            else:
                status_text = "待确认"
                status_color = ft.colors.ORANGE

            # 签名图片（对齐 uniapp：有 signArea 时展示签名）
            sign_controls: list[ft.Control] = []
            if sign_area:
                sign_src = (
                    sign_area if sign_area.startswith("http")
                    else f"{app_state.host}/jeecg-boot/sys/common/static/{sign_area}"
                )
                sign_controls.append(
                    ft.Row(
                        controls=[
                            ft.Text("签名：", size=11, color=ft.colors.GREY_600),
                            ft.Image(src=sign_src, height=40, fit=ft.ImageFit.CONTAIN),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4,
                    )
                )
                sign_time = m.get("updateTime") or m.get("signTime", "")
                if sign_time:
                    sign_controls.append(
                        ft.Text(f"签字时间：{sign_time}", size=11, color=ft.colors.GREY_500)
                    )

            def _make_measure_click(item_data):
                async def _click(e):
                    if disabled:
                        return
                    # 无操作权限时提示（对齐用户预期）
                    has_flag = bool(item_data.get("flag", True))
                    if not has_flag:
                        page.snack_bar = ft.SnackBar(ft.Text("暂无操作权限"), open=True)
                        await page.update_async()
                        return
                    await _go_measure_sign(item_data)
                return _click

            rows.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row([
                                ft.Text(m.get("aqcs", ""), size=12, expand=True),
                                ft.Container(
                                    content=ft.Text(status_text, size=11, color=ft.colors.WHITE),
                                    bgcolor=status_color,
                                    border_radius=4,
                                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                ),
                            ]),
                            *sign_controls,
                        ],
                        spacing=4,
                    ),
                    padding=12,
                    bgcolor=ft.colors.GREY_50,
                    border_radius=8,
                    margin=ft.margin.only(bottom=4),
                    on_click=_make_measure_click(m),
                    ink=not disabled,
                )
            )

        return ft.ListView(controls=rows, expand=True)

    async def _go_measure_sign(item: dict):
        """跳转安全措施签名页"""
        import json
        page.go(f"/ticket/sign?mode=assessment&info={json.dumps(item)}&type={type_value}")

    # --- 安全交底 ---
    async def _build_clarification_section() -> ft.Control:
        disabled = current_step[0] >= 3
        try:
            confess_list = await svc.get_confess(config.api_prefix, ticket_id)
            items = confess_list if isinstance(confess_list, list) else []
        except Exception:
            items = []

        rows: list[ft.Control] = [
            ft.Text("安全交底(请按顺序审批)", size=14, weight=ft.FontWeight.BOLD),
        ]

        # API 返回分组结构 [{title, object: [{personText, status, statusText, flag, ...}]}]
        for group in items:
            group_title = group.get("title", "")
            persons = group.get("object", [])
            if not isinstance(persons, list):
                persons = []

            person_tiles = []
            for p in persons:
                p_status = p.get("status", "")
                p_status_text = p.get("statusText", "待签名" if str(p_status) != "2" else "已签名")
                p_color = ft.colors.GREEN if str(p_status) == "2" else ft.colors.ORANGE
                update_time = p.get("updateTime", "")

                subtitle_parts = []
                if str(p_status) == "2" and update_time:
                    subtitle_parts.append(update_time)
                subtitle_parts.append(p_status_text)

                def _make_confess_click(person_data):
                    async def _click(e):
                        # 已签名或步骤已完成：静默（只查看）
                        if str(person_data.get("status")) == "2" or disabled:
                            return
                        if not person_data.get("flag"):
                            page.snack_bar = ft.SnackBar(ft.Text("暂无操作权限"), open=True)
                            await page.update_async()
                            return
                        await _go_confess_sign(person_data)
                    return _click

                person_tiles.append(
                    ft.ListTile(
                        title=ft.Text(p.get("personText", ""), size=13),
                        subtitle=ft.Text(" ".join(subtitle_parts), size=11, color=p_color),
                        on_click=_make_confess_click(p),
                    )
                )

            rows.append(
                ft.ExpansionTile(
                    title=ft.Text(group_title, size=13, weight=ft.FontWeight.W_500),
                    controls=person_tiles if person_tiles else [
                        ft.Container(content=ft.Text("暂无", size=12, color=ft.colors.GREY_500), padding=12)
                    ],
                    initially_expanded=len(rows) == 1,  # 第一组默认展开
                )
            )

        if not disabled and items:
            async def _submit_confess(e):
                try:
                    await svc.confess_submit(config.api_prefix, ticket_id)
                    page.snack_bar = ft.SnackBar(ft.Text("提交成功"), open=True)
                    await _load_detail()
                except Exception as ex:
                    page.snack_bar = ft.SnackBar(ft.Text(f"失败：{ex}"), open=True)
                    await page.update_async()

            rows.append(
                ft.ElevatedButton(
                    "提交安全交底",
                    on_click=_submit_confess,
                    bgcolor=ft.colors.BLUE,
                    color=ft.colors.WHITE,
                )
            )

        return ft.ListView(controls=rows, expand=True)

    async def _go_confess_sign(item: dict):
        import json
        page.go(f"/ticket/sign?mode=confess&info={json.dumps(item)}&type={type_value}")

    # --- 作业审批 ---
    async def _build_approval_section() -> ft.Control:
        disabled = current_step[0] >= 4
        username = app_state.user_info.get("username", "")

        try:
            approve_list = await svc.get_approve(config.api_prefix, ticket_id)
            items = approve_list if isinstance(approve_list, list) else []
        except Exception:
            items = []

        rows: list[ft.Control] = [
            ft.Text("安全审批(请按顺序审批)", size=14, weight=ft.FontWeight.BOLD),
        ]

        # API 返回分组结构 [{title, object: [{personText, status, statusText, flag, applyTime, ...}]}]
        approve_all_done = True
        for group in items:
            group_title = group.get("title", "")
            persons = group.get("object", [])
            if not isinstance(persons, list):
                persons = []

            person_tiles = []
            for p in persons:
                p_status = p.get("status", "")
                if str(p_status) != "2":
                    approve_all_done = False
                p_status_text = p.get("statusText", "待审批" if str(p_status) != "2" else "已审批")
                p_color = ft.colors.GREEN if str(p_status) == "2" else ft.colors.ORANGE
                apply_time = p.get("applyTime", "")

                subtitle_parts = []
                if str(p_status) == "2" and apply_time:
                    subtitle_parts.append(apply_time)
                subtitle_parts.append(p_status_text)

                def _make_approve_click(person_data):
                    async def _click(e):
                        if str(person_data.get("status")) == "2" or disabled:
                            return
                        if not person_data.get("flag"):
                            page.snack_bar = ft.SnackBar(ft.Text("暂无操作权限"), open=True)
                            await page.update_async()
                            return
                        await _go_approve_sign(person_data)
                    return _click

                person_tiles.append(
                    ft.ListTile(
                        title=ft.Text(p.get("personText", ""), size=13),
                        subtitle=ft.Text(" ".join(subtitle_parts), size=11, color=p_color),
                        on_click=_make_approve_click(p),
                    )
                )

            rows.append(
                ft.ExpansionTile(
                    title=ft.Text(group_title, size=13, weight=ft.FontWeight.W_500),
                    controls=person_tiles if person_tiles else [
                        ft.Container(content=ft.Text("暂无", size=12, color=ft.colors.GREY_500), padding=12)
                    ],
                    initially_expanded=len(rows) == 1,
                )
            )

        # 作业状态显示 + 控制按钮
        work_status = str(base_info.get("status", ""))
        status_map = {"5": "暂停", "2": "作业中", "3": "已完成"}
        status_text = status_map.get(work_status, "未开始")
        start_time = base_info.get("startTime", "") or ""
        end_time = base_info.get("dhEndTime", "") or ""

        rows.append(ft.Divider())
        rows.append(ft.Text(f"作业状态：{status_text}", size=15, weight=ft.FontWeight.BOLD))
        rows.append(ft.Text(f"作业开始时间：{start_time or '--'}", size=13))
        rows.append(ft.Text(f"作业结束时间：{end_time or '--'}", size=13))

        # 作业控制按钮
        try:
            can_begin = await svc.check_begin_btn(config.api_prefix, ticket_id, username)
        except Exception:
            can_begin = None

        async def _begin_work(e):
            try:
                await svc.begin_ticket(config.api_prefix, ticket_id)
                page.snack_bar = ft.SnackBar(ft.Text("操作成功"), open=True)
                await _load_detail()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"失败：{ex}"), open=True)
                await page.update_async()

        async def _pause_work(e):
            try:
                await svc.pause_ticket(config.api_prefix, ticket_id)
                page.snack_bar = ft.SnackBar(ft.Text("操作成功"), open=True)
                await _load_detail()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"失败：{ex}"), open=True)
                await page.update_async()

        async def _complete_work(e):
            try:
                await svc.complete_ticket(config.api_prefix, ticket_id)
                page.snack_bar = ft.SnackBar(ft.Text("操作成功"), open=True)
                await _load_detail()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"失败：{ex}"), open=True)
                await page.update_async()

        rows.append(
            ft.Row(
                controls=[
                    ft.ElevatedButton("开始作业", on_click=_begin_work, bgcolor=ft.colors.GREEN, color=ft.colors.WHITE),
                    ft.ElevatedButton("暂停作业", on_click=_pause_work, bgcolor=ft.colors.ORANGE, color=ft.colors.WHITE),
                    ft.ElevatedButton("完成作业", on_click=_complete_work, bgcolor=ft.colors.RED, color=ft.colors.WHITE),
                ],
                spacing=8,
                wrap=True,
            )
        )

        return ft.ListView(controls=rows, expand=True)

    async def _go_approve_sign(item: dict):
        import json
        page.go(f"/ticket/sign?mode=approve&info={json.dumps(item)}&type={type_value}")

    # --- 作业验收 ---
    async def _build_acceptance_section() -> ft.Control:
        disabled = current_step[0] >= 5
        username = app_state.user_info.get("username", "")

        # 检查作业是否已完成（UniApp: status=='3' && dhEndTime）
        work_status = str(base_info.get("status", ""))
        dh_end_time = base_info.get("dhEndTime", "")
        if work_status != "3" or not dh_end_time:
            return ft.Container(
                content=ft.Text("请先完成作业!", color=ft.colors.GREY_500),
                padding=20,
            )

        try:
            accept_result = await svc.get_acceptance(config.api_prefix, ticket_id, username)
            # API 可能返回数组或单个对象
            if isinstance(accept_result, list):
                items = accept_result
            elif isinstance(accept_result, dict):
                items = [accept_result]
            else:
                items = []
        except Exception:
            items = []

        rows: list[ft.Control] = [
            ft.Text("作业验收", size=14, weight=ft.FontWeight.BOLD),
        ]

        # 分组结构 [{title, object: [{personText, status, statusText, flag, signTime, ...}]}]
        for group in items:
            group_title = group.get("title", "")
            persons = group.get("object", [])
            if not isinstance(persons, list):
                persons = []

            person_tiles = []
            for p in persons:
                p_status = p.get("status", "")
                p_status_text = p.get("statusText", "待验收" if str(p_status) != "2" else "已验收")
                p_color = ft.colors.GREEN if str(p_status) == "2" else ft.colors.ORANGE
                sign_time = p.get("signTime", "")

                subtitle_parts = []
                if str(p_status) == "2" and sign_time:
                    subtitle_parts.append(sign_time)
                subtitle_parts.append(p_status_text)

                def _make_acceptance_click(person_data):
                    async def _click(e):
                        if str(person_data.get("status")) == "2" or disabled:
                            return
                        if not person_data.get("flag"):
                            page.snack_bar = ft.SnackBar(ft.Text("暂无操作权限"), open=True)
                            await page.update_async()
                            return
                        await _go_acceptance_sign(person_data)
                    return _click

                person_tiles.append(
                    ft.ListTile(
                        title=ft.Text(p.get("personText", ""), size=13),
                        subtitle=ft.Text(" ".join(subtitle_parts), size=11, color=p_color),
                        on_click=_make_acceptance_click(p),
                    )
                )

            rows.append(
                ft.ExpansionTile(
                    title=ft.Text(group_title, size=13, weight=ft.FontWeight.W_500),
                    controls=person_tiles if person_tiles else [
                        ft.Container(content=ft.Text("暂无", size=12, color=ft.colors.GREY_500), padding=12)
                    ],
                    initially_expanded=len(rows) == 1,
                )
            )

        if not disabled and items:
            async def _submit_acceptance(e):
                try:
                    await svc.acceptance_submit(config.api_prefix, ticket_id)
                    page.snack_bar = ft.SnackBar(ft.Text("验收提交成功"), open=True)
                    await _load_detail()
                except Exception as ex:
                    page.snack_bar = ft.SnackBar(ft.Text(f"失败：{ex}"), open=True)
                    await page.update_async()

            rows.append(
                ft.ElevatedButton(
                    "提交验收",
                    on_click=_submit_acceptance,
                    bgcolor=ft.colors.BLUE,
                    color=ft.colors.WHITE,
                )
            )

        return ft.ListView(controls=rows, expand=True)

    async def _go_acceptance_sign(item: dict):
        import json
        page.go(f"/ticket/sign?mode=acceptance&info={json.dumps(item)}&type={type_value}")

    # --- 组装页面 ---
    title_text = base_info.get("zyzbh", config.name)

    body = ft.Column(
        controls=[
            # 步骤指示器
            ft.Container(
                content=step_indicator,
                padding=ft.padding.symmetric(horizontal=8, vertical=12),
                bgcolor=ft.colors.WHITE,
            ),
            # 6 宫格
            grid_container,
            # 摄像头标题
            ft.Container(
                content=ft.Text("摄像头列表", size=14, weight=ft.FontWeight.BOLD),
                padding=ft.padding.only(left=16, top=12, bottom=4),
            ),
            camera_column,
        ],
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    view = ft.View(
        route="/ticket/detail",
        appbar=ft.AppBar(
            title=ft.Text(title_text),
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE,
        ),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    # 首次加载
    await _load_detail()

    return view
