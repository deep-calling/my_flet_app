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
from components.sign_pad import SignPad
from components.image_upload import ImageUpload


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

    # 当前打开的 BottomSheet + step index，用于提交/新增成功后关闭并重新打开以刷新
    current_bs: list[ft.BottomSheet | None] = [None]
    current_section_index: list[int] = [-1]

    def _close_current_bs():
        """关闭当前 BottomSheet（只设置 open=False，让 Flet 自己收尾，不要主动从 overlay 移除，
        否则客户端会因为状态不同步而渲染空白）。"""
        bs = current_bs[0]
        if bs is not None:
            try:
                bs.open = False
            except Exception:
                pass
        current_bs[0] = None
        current_section_index[0] = -1

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

        # 加载证书编号（动火人/监护人），通过证书表 id 换取 zsbh
        for code in ("dhzsbh", "jhrzsbh"):
            ids_str = base_info.get(code, "")
            if not ids_str:
                continue
            try:
                ids = [i for i in str(ids_str).split(",") if i]
                if not ids:
                    continue
                limit_in = "','".join(ids)
                res = await svc.get_table_data({
                    "table": "tb_base_certificate",
                    "columns": "GROUP_CONCAT(zsbh) zsbh",
                    "limits": f" id in ('{limit_in}')",
                })
                rows_ = res if isinstance(res, list) else []
                if rows_ and isinstance(rows_[0], dict) and rows_[0].get("zsbh"):
                    base_info[f"{code}_text"] = rows_[0]["zsbh"]
                else:
                    base_info[f"{code}_text"] = ids_str  # 旧版兼容
            except Exception:
                base_info[f"{code}_text"] = ids_str

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
        # 先关掉已有的 section BottomSheet
        old_bs = current_bs[0]
        if old_bs is not None:
            try:
                old_bs.open = False
            except Exception:
                pass
            current_bs[0] = None
            current_section_index[0] = -1
            try:
                await page.update_async()
            except Exception:
                pass

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

        def _close_self(_e=None):
            _close_current_bs()
            try:
                page.update()
            except Exception:
                pass

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
                                ft.IconButton(ft.icons.CLOSE, on_click=_close_self),
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
            on_dismiss=_close_self,
        )
        current_bs[0] = bs
        current_section_index[0] = index
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
            # 证书类字段优先用 _text（证书编号而非证书 id）
            if f.key in ("dhzsbh", "jhrzsbh"):
                val = base_info.get(f"{f.key}_text", "") or base_info.get(f.key, "")
            else:
                val = base_info.get(f"{f.key}_dictText") or base_info.get(f.key, "")
            rows.append(readonly_field(f.label, str(val) if val else ""))

        return ft.ListView(controls=rows, expand=True, spacing=0)

    # --- 安全分析 ---
    async def _show_detection_detail(insp: dict):
        """动火分析项详情弹框（只读）。"""
        def _img_src(p: str) -> str:
            return p if p.startswith("http") else f"{app_state.host}/jeecg-boot/sys/common/static/{p}"

        sign_path = insp.get("signArea", "")
        sign_widget: ft.Control
        if sign_path:
            sign_widget = ft.Image(src=_img_src(sign_path), height=80, fit=ft.ImageFit.CONTAIN)
        else:
            sign_widget = ft.Text("未签名", size=12, color=ft.colors.GREY_500)

        # 现场照片（photo 可能是逗号分隔多张）
        photo_str = str(insp.get("photo", "") or "")
        photo_paths = [p for p in photo_str.split(",") if p]
        if photo_paths:
            photo_widget: ft.Control = ft.Row(
                controls=[
                    ft.Image(src=_img_src(p), width=80, height=80, fit=ft.ImageFit.COVER)
                    for p in photo_paths
                ],
                wrap=True, spacing=6, run_spacing=6,
            )
        else:
            photo_widget = ft.Text("无现场照片", size=12, color=ft.colors.GREY_500)

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
                        ft.Text("现场照片", size=13, weight=ft.FontWeight.W_500),
                        photo_widget,
                        ft.Text("分析人签字", size=13, weight=ft.FontWeight.W_500),
                        sign_widget,
                    ],
                    tight=True, spacing=6,
                    scroll=ft.ScrollMode.AUTO,
                ),
                height=460,
            ),
            actions=[ft.TextButton("关闭", on_click=lambda e: _close_dialog(dlg))],
        )
        page.dialog = dlg
        dlg.open = True
        await page.update_async()

    def _close_dialog(dlg):
        dlg.open = False
        page.update()

    async def _open_detection_form(existing: dict | None):
        """打开新增/编辑 安全检测 对话框"""
        is_edit = existing is not None
        data = dict(existing) if existing else {}

        # 按作业类型选择表单字段（盲板抽堵与其他类型不同）
        is_mbcd = config.code == "MBCD"

        form: dict[str, Any] = {
            "id": data.get("id", ""),
            "fxdmc": data.get("fxdmc", ""),
            "fxr": data.get("fxr", ""),
            "fxrName": data.get("fxrName", ""),
            "dbxqt": data.get("dbxqt", ""),
            "mbwzt": data.get("mbwzt", ""),
            "mbbh": data.get("mbbh", ""),
            "fxjg": data.get("fxjg", ""),
            "remark": data.get("remark", ""),
            "photo": data.get("photo", ""),
            "signArea": data.get("signArea", ""),
        }

        async def _on_sign(path: str):
            form["signArea"] = path

        sign_widget = SignPad(
            page, on_success=_on_sign, sign_image=form["signArea"], width=300, height=160,
        )

        initial_photos = [p for p in str(form["photo"]).split(",") if p]

        async def _on_photo(_p: str):
            form["photo"] = ",".join(photo_widget.uploaded_paths)

        photo_widget = ImageUpload(
            page, on_upload_success=_on_photo,
            initial_images=initial_photos, max_count=9,
        )

        fxdmc_field = ft.TextField(
            label="分析点名称", value=form["fxdmc"],
            on_change=lambda e: form.__setitem__("fxdmc", e.control.value),
            text_size=14, border_color=ft.colors.GREY_300, dense=True,
        )
        fxr_field = ft.TextField(
            label="分析人", value=form["fxrName"],
            on_change=lambda e: form.__setitem__("fxrName", e.control.value),
            text_size=14, border_color=ft.colors.GREY_300, dense=True,
        )

        extra_fields: list[ft.Control] = []
        if is_mbcd:
            mbwzt_upload = ImageUpload(
                page,
                on_upload_success=lambda p: _set_mbwzt(p),
                initial_images=[p for p in str(form["mbwzt"]).split(",") if p],
                max_count=3,
            )

            async def _set_mbwzt(_p):
                form["mbwzt"] = ",".join(mbwzt_upload.uploaded_paths)

            extra_fields.append(ft.Text("盲板位置图", size=13, weight=ft.FontWeight.W_500))
            extra_fields.append(mbwzt_upload)
            extra_fields.append(
                ft.TextField(
                    label="盲板编号", value=form["mbbh"],
                    on_change=lambda e: form.__setitem__("mbbh", e.control.value),
                    text_size=14, border_color=ft.colors.GREY_300, dense=True,
                )
            )
        else:
            extra_fields.append(
                ft.TextField(
                    label="代表性气体", value=form["dbxqt"],
                    on_change=lambda e: form.__setitem__("dbxqt", e.control.value),
                    text_size=14, border_color=ft.colors.GREY_300, dense=True,
                )
            )

        fxjg_field = ft.TextField(
            label="分析结果" + ("" if is_mbcd else " / %"),
            value=form["fxjg"],
            on_change=lambda e: form.__setitem__("fxjg", e.control.value),
            text_size=14, border_color=ft.colors.GREY_300, dense=True,
        )
        remark_field = ft.TextField(
            label="结果备注", value=form["remark"],
            multiline=True, min_lines=2, max_lines=4,
            on_change=lambda e: form.__setitem__("remark", e.control.value),
            text_size=14, border_color=ft.colors.GREY_300,
        )

        dlg_ref: list[ft.AlertDialog] = []

        async def _close(_e=None):
            if dlg_ref:
                dlg_ref[0].open = False
                await page.update_async()

        async def _confirm(_e):
            if not form["fxdmc"]:
                page.snack_bar = ft.SnackBar(ft.Text("请输入分析点名称"), open=True)
                await page.update_async()
                return
            if not form["fxrName"]:
                page.snack_bar = ft.SnackBar(ft.Text("请输入分析人"), open=True)
                await page.update_async()
                return

            payload = {k: v for k, v in form.items()}
            payload["ticketId"] = ticket_id
            try:
                if is_edit:
                    await svc.edit_inspection(config.api_prefix, payload)
                    msg = "编辑成功"
                else:
                    payload.pop("id", None)
                    await svc.add_inspection(config.api_prefix, payload)
                    msg = "添加成功"
                await _close()
                page.snack_bar = ft.SnackBar(ft.Text(msg), open=True)
                await _load_detail()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"失败：{ex}"), open=True)
                await page.update_async()

        body_col = ft.Column(
            controls=[
                fxdmc_field,
                fxr_field,
                *extra_fields,
                fxjg_field,
                remark_field,
                ft.Text("现场照片", size=13, weight=ft.FontWeight.W_500),
                photo_widget,
                ft.Text("分析人签字", size=13, weight=ft.FontWeight.W_500),
                sign_widget,
            ],
            tight=True, spacing=8, scroll=ft.ScrollMode.AUTO,
        )

        dlg = ft.AlertDialog(
            title=ft.Text("编辑安全检测" if is_edit else "添加安全检测"),
            content=ft.Container(content=body_col, width=340, height=480),
            actions=[
                ft.TextButton("取消", on_click=lambda e: _close()),
                ft.TextButton("确认", on_click=_confirm),
            ],
        )
        dlg_ref.append(dlg)
        page.dialog = dlg
        dlg.open = True
        await page.update_async()

    async def _build_detection_section() -> ft.Control:
        """安全分析步骤"""
        permissions = False
        try:
            inspections = await svc.get_inspection_by_id(config.api_prefix, ticket_id)
            if isinstance(inspections, dict):
                items = inspections.get("data", []) or []
                permissions = inspections.get("permissions", False)
            elif isinstance(inspections, list):
                items = inspections
            else:
                items = []
        except Exception:
            items = []

        need_analysis = str(base_info.get("sfxyaqjc", config.analysis_default or "1")) == "1"
        if not need_analysis:
            return ft.Container(
                content=ft.Text("不需要进行分析!", color=ft.colors.GREY_500),
                alignment=ft.alignment.center,
                padding=20,
            )

        disabled = current_step[0] >= 1

        rows: list[ft.Control] = []
        if not items:
            rows.append(ft.Text("暂无分析数据", color=ft.colors.GREY_500))
        else:
            for insp in items:
                def _make_edit_click(data):
                    async def _click(e):
                        if permissions and not disabled:
                            await _open_detection_form(data)
                        else:
                            await _show_detection_detail(data)
                    return _click

                rows.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"分析点: {insp.get('fxdmc', '')}", size=13, weight=ft.FontWeight.W_500),
                            ft.Text(f"分析人: {insp.get('fxrName', '')}", size=12, color=ft.colors.GREY_600),
                            ft.Text(
                                f"{'盲板编号' if config.code == 'MBCD' else '代表性气体'}: "
                                f"{insp.get('mbbh', '') if config.code == 'MBCD' else insp.get('dbxqt', '')}",
                                size=12, color=ft.colors.GREY_600,
                            ),
                            ft.Text(f"分析结果: {insp.get('fxjg', '')}", size=12, color=ft.colors.GREY_600),
                            ft.Text(f"提交时间: {insp.get('submitTime', '')}", size=12, color=ft.colors.GREY_600),
                        ], spacing=4),
                        padding=12,
                        bgcolor=ft.colors.GREY_50,
                        border_radius=8,
                        margin=ft.margin.only(bottom=8),
                        on_click=_make_edit_click(insp),
                        ink=True,
                    )
                )

        async def _submit_detection(e):
            try:
                await svc.submit_inspection(config.api_prefix, ticket_id)
                # 先关闭 BottomSheet 并刷掉客户端状态，再 reload —— 避免点击事件仍在
                # 处理时改动控件树导致 Flet 渲染空白
                bs = current_bs[0]
                if bs is not None:
                    try:
                        bs.open = False
                    except Exception:
                        pass
                    current_bs[0] = None
                    current_section_index[0] = -1
                    try:
                        await page.update_async()
                    except Exception:
                        pass
                page.snack_bar = ft.SnackBar(ft.Text("提交成功"), open=True)
                await _load_detail()
            except Exception as ex:
                import traceback
                traceback.print_exc()
                page.snack_bar = ft.SnackBar(ft.Text(f"失败：{ex}"), open=True)
                try:
                    await page.update_async()
                except Exception:
                    pass

        async def _add_detection(e):
            await _open_detection_form(None)

        # 操作按钮：添加安全检测 + 提交
        if permissions and not disabled:
            btn_row: list[ft.Control] = [
                ft.ElevatedButton(
                    "添加安全检测", on_click=_add_detection,
                    bgcolor=ft.colors.BLUE, color=ft.colors.WHITE, expand=True,
                ),
            ]
            if items:
                btn_row.append(
                    ft.ElevatedButton(
                        "提交", on_click=_submit_detection,
                        bgcolor=ft.colors.GREEN, color=ft.colors.WHITE, expand=True,
                    )
                )
            rows.append(ft.Row(controls=btn_row, spacing=8))

        return ft.ListView(controls=rows, expand=True)

    # --- 安全评估 ---
    async def _build_assessment_section() -> ft.Control:
        """安全评估 — 危害辨识 + 安全措施 + 作业人签字"""
        permissions = False
        zyr_permissions = False
        measure_step = 0

        try:
            harm_list = await svc.get_dict_harm(config.api_prefix, ticket_id)
            if not isinstance(harm_list, list):
                harm_list = []
        except Exception:
            harm_list = []

        zyr_sign_area_init = ""
        try:
            measures = await svc.get_measure_by_id(config.api_prefix, ticket_id)
            if isinstance(measures, dict):
                measure_items = measures.get("data", []) or []
                permissions = measures.get("permissions", False)
                zyr_permissions = measures.get("zyrPermissions", False)
                measure_step = measures.get("step", 0)
                zyr_sign_area_init = measures.get("zyrSignArea", "") or ""
            elif isinstance(measures, list):
                measure_items = measures
            else:
                measure_items = []
        except Exception:
            measure_items = []

        can_edit = str(measure_step) == "2"

        # 已选中的危害辨识 value 列表
        whbs_raw = str(base_info.get("whbs", "") or "")
        existing_whbs_values = [v for v in whbs_raw.split(",") if v]
        # 展示文本（优先用 _dictText，否则用 value 直接显示）
        whbs_text_init = (
            base_info.get("whbs_dictText")
            or ",".join(
                h.get("text", "") for h in harm_list
                if str(h.get("value", "")) in existing_whbs_values
            )
            or ""
        )
        # 可变状态
        selected_whbs_values = list(existing_whbs_values)
        zyr_sign_area_state = [zyr_sign_area_init]
        whbs_display = ft.Text(
            whbs_text_init or "未选择", size=12,
            color=ft.colors.GREY_700 if whbs_text_init else ft.colors.GREY_500,
        )

        async def _open_harm_picker(_e):
            if not permissions:
                page.snack_bar = ft.SnackBar(ft.Text("暂无操作权限"), open=True)
                await page.update_async()
                return
            if not harm_list:
                page.snack_bar = ft.SnackBar(ft.Text("暂无可选危害辨识项"), open=True)
                await page.update_async()
                return

            local_selected = set(selected_whbs_values)
            check_rows: list[ft.Control] = []

            def _make_checkbox(item_value: str, item_text: str):
                def _on_change(e):
                    if e.control.value:
                        local_selected.add(item_value)
                    else:
                        local_selected.discard(item_value)
                return ft.Checkbox(
                    label=item_text,
                    value=item_value in local_selected,
                    on_change=_on_change,
                )

            for h in harm_list:
                v = str(h.get("value", ""))
                t = h.get("text", "")
                check_rows.append(_make_checkbox(v, t))

            bs_ref: list[ft.BottomSheet] = []

            async def _close_bs():
                if bs_ref:
                    bs_ref[0].open = False
                    await page.update_async()

            async def _confirm(_ev):
                selected_whbs_values.clear()
                selected_whbs_values.extend(sorted(local_selected))
                whbs_display.value = ",".join(
                    h.get("text", "") for h in harm_list
                    if str(h.get("value", "")) in selected_whbs_values
                ) or "未选择"
                whbs_display.color = ft.colors.GREY_700 if selected_whbs_values else ft.colors.GREY_500
                await _close_bs()
                await page.update_async()

            bs = ft.BottomSheet(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row([
                                ft.Text("选择危害辨识", size=15, weight=ft.FontWeight.BOLD),
                                ft.IconButton(ft.icons.CLOSE, on_click=lambda e: _close_bs()),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(height=1),
                            ft.ListView(controls=check_rows, expand=True, spacing=0),
                            ft.ElevatedButton(
                                "确认", on_click=_confirm,
                                bgcolor=ft.colors.BLUE, color=ft.colors.WHITE,
                                width=None, expand=True,
                            ),
                        ],
                        spacing=8, expand=True,
                    ),
                    padding=16,
                    height=page.height * 0.7 if page.height else 500,
                ),
                open=True,
            )
            bs_ref.append(bs)
            page.overlay.append(bs)
            await page.update_async()

        rows: list[ft.Control] = [
            ft.Text("危害辨识", size=14, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(content=whbs_display, expand=True),
                        ft.Icon(ft.icons.CHEVRON_RIGHT, color=ft.colors.GREY_500),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=12,
                bgcolor=ft.colors.GREY_50,
                border_radius=8,
                margin=ft.margin.only(bottom=8),
                on_click=_open_harm_picker,
                ink=True,
            ),
            ft.Text("安全措施", size=14, weight=ft.FontWeight.BOLD),
        ]

        measure_count = len(measure_items)
        for idx, m in enumerate(measure_items):
            is_last = idx == measure_count - 1
            sign_area = m.get("signArea", "")
            selected = str(m.get("selected", ""))

            # 状态文本计算
            if selected == "2":
                status_text = "不涉及"
                status_color = ft.colors.GREY_600
            elif selected == "1" and sign_area:
                status_text = "涉及"
                status_color = ft.colors.GREEN
            elif sign_area:
                status_text = "已确认"
                status_color = ft.colors.GREEN
            else:
                status_text = "待确认"
                status_color = ft.colors.ORANGE

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

            def _make_measure_click(item_data, last_flag):
                async def _click(e):
                    if not can_edit:
                        page.snack_bar = ft.SnackBar(ft.Text("已提交的流程不可再修改"), open=True)
                        await page.update_async()
                        return
                    if not permissions:
                        page.snack_bar = ft.SnackBar(ft.Text("暂无操作权限"), open=True)
                        await page.update_async()
                        return
                    sign_mode = "assessment_other" if last_flag else "assessment"
                    await _go_measure_sign(item_data, sign_mode)
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
                    on_click=_make_measure_click(m, is_last),
                    ink=can_edit,
                )
            )

        # 作业人签字区域
        rows.append(ft.Text("作业人签字", size=14, weight=ft.FontWeight.BOLD))

        async def _on_zyr_sign(path: str):
            if not zyr_permissions:
                page.snack_bar = ft.SnackBar(ft.Text("您没有权限签字"), open=True)
                await page.update_async()
                return
            zyr_sign_area_state[0] = path

        zyr_sign_widget = SignPad(
            page,
            on_success=_on_zyr_sign,
            sign_image=zyr_sign_area_init,
            disabled=not can_edit or not zyr_permissions,
            width=320, height=140,
        )
        rows.append(
            ft.Container(
                content=zyr_sign_widget,
                padding=12, bgcolor=ft.colors.WHITE,
                border_radius=8, margin=ft.margin.only(bottom=8),
            )
        )

        # 保存/提交（sign=2 保存，sign=1 提交）
        async def _save_or_submit(sign_value: int):
            if not can_edit:
                page.snack_bar = ft.SnackBar(ft.Text("已提交的流程不可再修改"), open=True)
                await page.update_async()
                return
            whbs_str = ",".join(selected_whbs_values)
            if not whbs_str:
                page.snack_bar = ft.SnackBar(ft.Text("请选择作业危险辨识!"), open=True)
                await page.update_async()
                return
            if sign_value == 1:
                # 提交校验：作业人签字 + 所有措施已确认
                if not zyr_sign_area_state[0]:
                    page.snack_bar = ft.SnackBar(ft.Text("请作业人进行签字!"), open=True)
                    await page.update_async()
                    return
                for m in measure_items:
                    aqcs = str(m.get("aqcs", ""))
                    sel = str(m.get("selected", ""))
                    sig = m.get("signArea", "")
                    is_other = "其他安全措施" in aqcs
                    if is_other:
                        if sel != "2" and not sig:
                            page.snack_bar = ft.SnackBar(ft.Text("请确认所有的安全措施!"), open=True)
                            await page.update_async()
                            return
                    else:
                        if not sig:
                            page.snack_bar = ft.SnackBar(ft.Text("请确认所有的安全措施!"), open=True)
                            await page.update_async()
                            return

            params = {
                "id": ticket_id,
                "measuresList": measure_items,
                "sign": sign_value,
                "whbs": whbs_str,
                "zyrSignArea": zyr_sign_area_state[0],
            }
            try:
                if sign_value == 1:
                    await svc.submit_assessment(config.api_prefix, params)
                else:
                    await svc.save_assessment(config.api_prefix, params)
                page.snack_bar = ft.SnackBar(
                    ft.Text("提交成功" if sign_value == 1 else "保存成功"), open=True,
                )
                await _load_detail()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"失败：{ex}"), open=True)
                await page.update_async()

        if can_edit and (permissions or zyr_permissions):
            rows.append(
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            "保存",
                            on_click=lambda e: page.run_task(_save_or_submit, 2),
                            bgcolor=ft.colors.ORANGE, color=ft.colors.WHITE, expand=True,
                        ),
                        ft.ElevatedButton(
                            "提交",
                            on_click=lambda e: page.run_task(_save_or_submit, 1),
                            bgcolor=ft.colors.BLUE, color=ft.colors.WHITE, expand=True,
                        ),
                    ],
                    spacing=8,
                )
            )

        return ft.ListView(controls=rows, expand=True)

    async def _go_measure_sign(item: dict, sign_mode: str = "assessment"):
        """跳转安全措施签名页"""
        import json
        page.go(f"/ticket/sign?mode={sign_mode}&info={json.dumps(item)}&type={type_value}")

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
                        # 对齐 uniapp：无 flag → 权限提示；有 flag → 进入详情（已签名则只读）
                        if not person_data.get("flag"):
                            page.snack_bar = ft.SnackBar(ft.Text("您未有权限！"), open=True)
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

        # ── 审批流程卡片 ──
        approve_all_done = True
        group_widgets: list[ft.Control] = []
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
                is_done = str(p_status) == "2"
                p_status_text = p.get("statusText", "已审批" if is_done else "待审批")
                apply_time = p.get("applyTime", "")

                def _make_approve_click(person_data):
                    async def _click(e):
                        if not person_data.get("flag"):
                            page.snack_bar = ft.SnackBar(ft.Text("您未有权限！"), open=True)
                            await page.update_async()
                            return
                        await _go_approve_sign(person_data)
                    return _click

                # 每个审批人：左侧图标 + 姓名/时间 + 右侧状态标签
                person_tiles.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.icons.CHECK_CIRCLE if is_done else ft.icons.RADIO_BUTTON_UNCHECKED,
                                    size=20,
                                    color=ft.colors.GREEN if is_done else ft.colors.GREY_400,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(p.get("personText", ""), size=13, weight=ft.FontWeight.W_500),
                                        ft.Text(
                                            apply_time if is_done and apply_time else "",
                                            size=11, color=ft.colors.GREY_500,
                                            visible=bool(is_done and apply_time),
                                        ),
                                    ],
                                    spacing=2, expand=True,
                                ),
                                ft.Container(
                                    content=ft.Text(p_status_text, size=11, color=ft.colors.WHITE),
                                    bgcolor=ft.colors.GREEN if is_done else ft.colors.ORANGE,
                                    border_radius=10,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        on_click=_make_approve_click(p),
                        ink=True,
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    )
                )

            group_widgets.append(
                ft.ExpansionTile(
                    title=ft.Text(group_title, size=13, weight=ft.FontWeight.W_500),
                    controls=person_tiles if person_tiles else [
                        ft.Container(content=ft.Text("暂无", size=12, color=ft.colors.GREY_500), padding=12)
                    ],
                    initially_expanded=len(group_widgets) == 0,
                    tile_padding=ft.padding.symmetric(horizontal=8),
                )
            )

        approval_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.icons.APPROVAL_OUTLINED, size=18, color=ft.colors.BLUE),
                            ft.Text("审批流程", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text("（请按顺序审批）", size=11, color=ft.colors.GREY_500),
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=1, color=ft.colors.GREY_200),
                    *group_widgets,
                ],
                spacing=4,
            ),
            padding=12,
            bgcolor=ft.colors.WHITE,
            border_radius=8,
        )

        # ── 作业状态卡片 ──
        work_status = str(base_info.get("status", ""))
        status_map = {
            "5": ("暂停", ft.colors.ORANGE, ft.icons.PAUSE_CIRCLE_OUTLINE),
            "2": ("作业中", ft.colors.BLUE, ft.icons.PLAY_CIRCLE_OUTLINE),
            "3": ("已完成", ft.colors.GREEN, ft.icons.CHECK_CIRCLE_OUTLINE),
            "4": ("已作废", ft.colors.RED, ft.icons.CANCEL_OUTLINED),
        }
        default_status = ("未开始", ft.colors.GREY_600, ft.icons.SCHEDULE_OUTLINED)
        status_text, status_color, status_icon = status_map.get(work_status, default_status)
        start_time = base_info.get("startTime", "") or ""
        end_time = base_info.get("dhEndTime", "") or base_info.get("endTime", "") or ""

        # 权限检查
        try:
            begin_res = await svc.check_begin_btn(config.api_prefix, ticket_id, username)
            check_status = str(begin_res) if begin_res is not None else "2"
        except Exception:
            check_status = "2"
        has_op_permission = check_status == "1"

        def _precheck_op() -> str | None:
            if not has_op_permission:
                return "您无权限操作"
            if not approve_all_done:
                return "需要所有人都审批通过,才可操作"
            if work_status == "3":
                return "作业票已完成"
            if work_status == "4":
                return "作业票已作废"
            return None

        async def _call_op(coro_factory, ok_msg: str):
            msg = _precheck_op()
            if msg:
                page.snack_bar = ft.SnackBar(ft.Text(msg), open=True)
                await page.update_async()
                return
            try:
                await coro_factory()
                page.snack_bar = ft.SnackBar(ft.Text(ok_msg), open=True)
                await _load_detail()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"失败：{ex}"), open=True)
                await page.update_async()

        async def _begin_work(e):
            await _call_op(
                lambda: svc.begin_ticket(config.api_prefix, ticket_id), "操作成功",
            )

        async def _pause_work(e):
            await _call_op(
                lambda: svc.pause_ticket(config.api_prefix, ticket_id), "操作成功",
            )

        async def _complete_work(e):
            await _call_op(
                lambda: svc.complete_ticket(config.api_prefix, ticket_id), "操作成功",
            )

        # 根据当前状态决定按钮可用性
        can_begin = work_status not in ("2", "3", "4")
        can_pause = work_status == "2"
        can_complete = work_status in ("2", "5")

        op_buttons: list[ft.Control] = []
        if can_begin:
            op_buttons.append(
                ft.ElevatedButton(
                    "开始作业", icon=ft.icons.PLAY_ARROW,
                    on_click=_begin_work,
                    bgcolor=ft.colors.GREEN, color=ft.colors.WHITE, expand=True,
                )
            )
        if can_pause:
            op_buttons.append(
                ft.ElevatedButton(
                    "暂停作业", icon=ft.icons.PAUSE,
                    on_click=_pause_work,
                    bgcolor=ft.colors.ORANGE, color=ft.colors.WHITE, expand=True,
                )
            )
        if can_complete:
            op_buttons.append(
                ft.ElevatedButton(
                    "完成作业", icon=ft.icons.STOP,
                    on_click=_complete_work,
                    bgcolor=ft.colors.RED, color=ft.colors.WHITE, expand=True,
                )
            )

        status_card_controls: list[ft.Control] = [
            ft.Row(
                controls=[
                    ft.Icon(status_icon, size=22, color=status_color),
                    ft.Text("作业状态", size=14, weight=ft.FontWeight.BOLD, expand=True),
                    ft.Container(
                        content=ft.Text(status_text, size=12, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD),
                        bgcolor=status_color,
                        border_radius=12,
                        padding=ft.padding.symmetric(horizontal=12, vertical=4),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Divider(height=1, color=ft.colors.GREY_200),
            ft.Row([
                ft.Text("开始时间", size=12, color=ft.colors.GREY_600, width=70),
                ft.Text(start_time or "--", size=12),
            ]),
            ft.Row([
                ft.Text("结束时间", size=12, color=ft.colors.GREY_600, width=70),
                ft.Text(end_time or "--", size=12),
            ]),
        ]
        if op_buttons:
            status_card_controls.append(ft.Container(height=4))
            status_card_controls.append(ft.Row(controls=op_buttons, spacing=8))

        status_card = ft.Container(
            content=ft.Column(controls=status_card_controls, spacing=6),
            padding=12,
            bgcolor=ft.colors.WHITE,
            border_radius=8,
        )

        return ft.ListView(
            controls=[approval_card, ft.Container(height=8), status_card],
            expand=True,
        )

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
                        if not person_data.get("flag"):
                            page.snack_bar = ft.SnackBar(ft.Text("您未有权限！"), open=True)
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

    # --- 签名页返回后刷新 ---
    async def _on_sign_return():
        """签名提交成功后回调：关闭当前 BottomSheet → 重新加载详情 → 重新打开该步骤面板"""
        section_idx = current_section_index[0]
        _close_current_bs()
        try:
            await page.update_async()
        except Exception:
            pass
        await _load_detail()
        if section_idx >= 0:
            await _show_section(section_idx)

    page._ticket_detail_refresh = _on_sign_return

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
