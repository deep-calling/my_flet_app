"""作业票签名页 — 5 种签名模式统一处理

签名模式 (mode):
- confess: 安全交底签名
- assessment: 安全措施签名
- assessment_other: 其他安全措施签名（双签名）
- approve: 审批签名
- acceptance: 验收签名
"""

from __future__ import annotations

import json
from typing import Any

import flet as ft

from pages.ticket.config import get_config_by_type_value
from services import ticket_service as svc
from components.sign_pad import SignPad
from components.image_upload import ImageUpload


# 模式标题映射
_MODE_TITLES = {
    "confess": "安全交底签名",
    "assessment": "安全措施确认",
    "assessment_other": "其他安全措施确认",
    "approve": "审批签名",
    "acceptance": "验收签名",
}


async def build_ticket_sign_page(
    page: ft.Page,
    mode: str,
    info_json: str,
    type_value: str,
) -> ft.View:
    """构建作业票签名页。"""
    config = get_config_by_type_value(type_value)
    if not config:
        return ft.View(route="/ticket/sign", controls=[ft.Text("未知类型")])

    try:
        info = json.loads(info_json) if info_json else {}
    except (json.JSONDecodeError, TypeError):
        info = {}

    ticket_id = info.get("ticketId", "")
    item_id = info.get("id", "")
    is_readonly = str(info.get("status", "")) == "2"

    aqcs_raw = str(info.get("aqcs", "") or "")
    # assessment_other: 后端存储 "其他安全措施：xxx"，编辑时剥离前缀
    aqcs_edit = aqcs_raw.split("其他安全措施：", 1)[-1] if mode == "assessment_other" else aqcs_raw

    form_data: dict[str, Any] = {
        "opinion": info.get("opinion", ""),
        "signArea": info.get("signArea", ""),
        "photo": info.get("photo", ""),
        "selected": str(info.get("selected", "")) if info.get("selected") else "",
        "aqcs": aqcs_edit,
        "applyStatus": info.get("applyStatus", ""),
    }
    sign_image_path = [""]
    title = _MODE_TITLES.get(mode, "签名")

    async def _on_sign_success(file_path: str):
        sign_image_path[0] = file_path
        form_data["signArea"] = file_path

    sign_pad = SignPad(
        page,
        on_success=_on_sign_success,
        sign_image=info.get("signArea", ""),
        disabled=is_readonly,
    )

    # 现场照片上传组件（confess/approve/acceptance 共用）
    async def _on_photo_uploaded(_file_path: str):
        form_data["photo"] = ",".join(photo_upload.uploaded_paths)

    initial_photos = [p for p in str(info.get("photo", "") or "").split(",") if p]
    photo_upload = ImageUpload(
        page,
        on_upload_success=_on_photo_uploaded,
        disabled=is_readonly,
        initial_images=initial_photos,
        max_count=9,
    )

    form_controls: list[ft.Control] = []

    if mode == "confess":
        form_controls.append(
            ft.Container(
                content=ft.Text(
                    "确认已经传达交底内容，已经向工作负责人和作业人员告知区域风险及预防措施",
                    size=13, color=ft.colors.BLUE_700, italic=True,
                ),
                padding=16, bgcolor=ft.colors.BLUE_50, border_radius=8,
            )
        )
        opinion_field = ft.TextField(
            value=form_data["opinion"], hint_text="请输入交底内容",
            multiline=True, min_lines=3, max_lines=6,
            on_change=lambda e: form_data.__setitem__("opinion", e.control.value),
            read_only=is_readonly,
            border_color=ft.colors.GREY_300, text_size=14,
        )
        form_controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("交底内容", size=14, weight=ft.FontWeight.W_500),
                    opinion_field,
                ], spacing=8),
                padding=16, bgcolor=ft.colors.WHITE,
            )
        )

    elif mode == "assessment":
        form_controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("安全措施", size=14, weight=ft.FontWeight.W_500),
                    ft.Text(form_data.get("aqcs", ""), size=13, color=ft.colors.GREY_700),
                ], spacing=8),
                padding=16, bgcolor=ft.colors.WHITE,
            )
        )
        rg = ft.RadioGroup(
            value=form_data.get("selected", ""),
            on_change=lambda e: form_data.__setitem__("selected", e.control.value),
            content=ft.Row([
                ft.Radio(value="1", label="涉及"),
                ft.Radio(value="2", label="不涉及"),
            ]),
        )
        if not is_readonly:
            form_controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("是否涉及", size=14, weight=ft.FontWeight.W_500),
                        rg,
                    ], spacing=8),
                    padding=16, bgcolor=ft.colors.WHITE,
                )
            )

    elif mode == "assessment_other":
        form_controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("其他安全措施", size=14, weight=ft.FontWeight.W_500),
                    ft.TextField(
                        value=form_data.get("aqcs", ""), hint_text="请输入安全措施",
                        multiline=True, min_lines=3,
                        on_change=lambda e: form_data.__setitem__("aqcs", e.control.value),
                        read_only=is_readonly,
                        border_color=ft.colors.GREY_300, text_size=14,
                    ),
                ], spacing=8),
                padding=16, bgcolor=ft.colors.WHITE,
            )
        )
        rg = ft.RadioGroup(
            value=form_data.get("selected", ""),
            on_change=lambda e: form_data.__setitem__("selected", e.control.value),
            content=ft.Row([
                ft.Radio(value="1", label="涉及"),
                ft.Radio(value="2", label="不涉及"),
            ]),
        )
        if not is_readonly:
            form_controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("是否涉及", size=14, weight=ft.FontWeight.W_500),
                        rg,
                    ], spacing=8),
                    padding=16, bgcolor=ft.colors.WHITE,
                )
            )

    elif mode == "approve":
        opinion_field = ft.TextField(
            value=form_data["opinion"], hint_text="请输入审批意见",
            multiline=True, min_lines=3, max_lines=6,
            on_change=lambda e: form_data.__setitem__("opinion", e.control.value),
            read_only=is_readonly,
            border_color=ft.colors.GREY_300, text_size=14,
        )
        form_controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("审批意见", size=14, weight=ft.FontWeight.W_500),
                    opinion_field,
                ], spacing=8),
                padding=16, bgcolor=ft.colors.WHITE,
            )
        )

        apply_status_options: list[dict] = []
        try:
            status_result = await svc.get_dict_apply_status(config.api_prefix)
            if isinstance(status_result, list):
                apply_status_options = [
                    {"text": r.get("title") or r.get("text", ""), "value": str(r.get("value", ""))}
                    for r in status_result
                ]
        except Exception:
            pass
        if not apply_status_options:
            apply_status_options = [{"text": "同意", "value": "1"}, {"text": "不同意", "value": "2"}]

        current_apply = str(form_data.get("applyStatus", ""))
        if is_readonly:
            apply_text = next(
                (o["text"] for o in apply_status_options if o["value"] == current_apply),
                current_apply or "-",
            )
            apply_widget: ft.Control = ft.Text(
                apply_text, size=14, color=ft.colors.BLACK,
            )
        else:
            apply_widget = ft.RadioGroup(
                value=current_apply,
                on_change=lambda e: form_data.__setitem__("applyStatus", e.control.value),
                content=ft.Row(
                    [ft.Radio(value=o["value"], label=o["text"]) for o in apply_status_options],
                    wrap=True,
                ),
            )
        form_controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("审批结果", size=14, weight=ft.FontWeight.W_500),
                    apply_widget,
                ], spacing=8),
                padding=16, bgcolor=ft.colors.WHITE,
            )
        )

    elif mode == "acceptance":
        form_controls.append(
            ft.Container(
                content=ft.Text(
                    "本许可证工作执行完毕，现场处于安全、清洁状态",
                    size=13, color=ft.colors.BLUE_700, italic=True,
                ),
                padding=16, bgcolor=ft.colors.BLUE_50, border_radius=8,
            )
        )
        opinion_field = ft.TextField(
            value=form_data["opinion"], hint_text="请输入验收意见",
            multiline=True, min_lines=3, max_lines=6,
            on_change=lambda e: form_data.__setitem__("opinion", e.control.value),
            read_only=is_readonly,
            border_color=ft.colors.GREY_300, text_size=14,
        )
        form_controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("验收意见", size=14, weight=ft.FontWeight.W_500),
                    opinion_field,
                ], spacing=8),
                padding=16, bgcolor=ft.colors.WHITE,
            )
        )

    # 签名区域
    form_controls.append(
        ft.Container(
            content=ft.Column([
                ft.Text("签名", size=14, weight=ft.FontWeight.W_500),
                sign_pad,
            ], spacing=8),
            padding=16, bgcolor=ft.colors.WHITE,
        )
    )

    # 现场照片：confess / approve / acceptance 都需要
    if mode in ("confess", "approve", "acceptance"):
        form_controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("现场照片", size=14, weight=ft.FontWeight.W_500),
                    photo_upload,
                ], spacing=8),
                padding=16, bgcolor=ft.colors.WHITE,
            )
        )

    async def _submit(e):
        if mode in ("assessment", "assessment_other") and not form_data.get("selected"):
            page.snack_bar = ft.SnackBar(ft.Text("请先确认是否涉及"), open=True)
            await page.update_async()
            return

        # assessment_other 选"不涉及"时无需签名
        _other_not_involved = (
            mode == "assessment_other" and str(form_data.get("selected", "")) == "2"
        )
        if not _other_not_involved:
            if not form_data.get("signArea") and not sign_image_path[0]:
                page.snack_bar = ft.SnackBar(ft.Text("请先签名"), open=True)
                await page.update_async()
                return

        if mode == "approve" and not form_data.get("applyStatus"):
            page.snack_bar = ft.SnackBar(ft.Text("请选择审批结果"), open=True)
            await page.update_async()
            return

        try:
            params: dict[str, Any] = {
                "id": item_id,
                "ticketId": ticket_id,
                "signArea": form_data.get("signArea", ""),
            }

            if mode == "confess":
                params["opinion"] = form_data.get("opinion", "")
                params["photo"] = form_data.get("photo", "")
                await svc.confess_apply(config.api_prefix, params)
            elif mode in ("assessment", "assessment_other"):
                params["selected"] = form_data.get("selected", "")
                aqcs_val = form_data.get("aqcs", "")
                if mode == "assessment_other":
                    # "不涉及" 时后端约定 aqcs 为 "其他安全措施：/"
                    if str(form_data.get("selected", "")) == "2":
                        aqcs_val = "/"
                    params["aqcs"] = f"其他安全措施：{aqcs_val}"
                else:
                    params["aqcs"] = aqcs_val
                await svc.measures_apply(config.api_prefix, params)
            elif mode == "approve":
                params["opinion"] = form_data.get("opinion", "")
                params["applyStatus"] = form_data.get("applyStatus", "")
                params["photo"] = form_data.get("photo", "")
                await svc.approve_apply(config.api_prefix, params)
            elif mode == "acceptance":
                params["opinion"] = form_data.get("opinion", "")
                params["photo"] = form_data.get("photo", "")
                await svc.sign_ticket(config.api_prefix, params)

            page.snack_bar = ft.SnackBar(ft.Text("提交成功"), open=True)
            await page.update_async()
            if len(page.views) > 1:
                page.views.pop()
                await page.update_async()

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"提交失败：{ex}"), open=True)
            await page.update_async()

    # 转办按钮（仅审批模式）
    appbar_actions: list[ft.Control] = []
    if mode == "approve" and not is_readonly:
        async def _forward(e):
            try:
                people = await svc.get_people_list_for_forward(config.api_prefix)
                people_list = people if isinstance(people, list) else []
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"加载人员失败：{ex}"), open=True)
                await page.update_async()
                return

            if not people_list:
                page.snack_bar = ft.SnackBar(ft.Text("暂无可转办人员"), open=True)
                await page.update_async()
                return

            dlg_ref: list[ft.AlertDialog] = []

            async def _close(_d):
                _d.open = False
                await page.update_async()

            async def _do_forward(person_id):
                try:
                    await svc.forward_approve(
                        config.api_prefix, {"id": item_id, "person": person_id}
                    )
                    if dlg_ref:
                        dlg_ref[0].open = False
                    page.snack_bar = ft.SnackBar(ft.Text("转办成功"), open=True)
                    await page.update_async()
                    if len(page.views) > 1:
                        page.views.pop()
                        await page.update_async()
                except Exception as ex:
                    page.snack_bar = ft.SnackBar(ft.Text(f"转办失败：{ex}"), open=True)
                    await page.update_async()

            def _make_forward_click(pid):
                async def _click(_e):
                    await _do_forward(pid)
                return _click

            tiles = []
            for p in people_list:
                display = (
                    p.get("xm")
                    or p.get("realname")
                    or p.get("name")
                    or p.get("username")
                    or ""
                )
                pid = p.get("id") or p.get("value") or p.get("userId", "")
                tiles.append(
                    ft.ListTile(
                        title=ft.Text(display or "(未命名)", size=14),
                        subtitle=ft.Text(p.get("username") or "", size=11, color=ft.colors.GREY_600),
                        on_click=_make_forward_click(pid),
                    )
                )

            dlg = ft.AlertDialog(
                title=ft.Text("选择转办人"),
                content=ft.Container(
                    content=ft.Column(tiles, scroll=ft.ScrollMode.AUTO, tight=True),
                    height=400, width=300,
                ),
                actions=[ft.TextButton("取消", on_click=lambda _e: _close(dlg))],
            )
            dlg_ref.append(dlg)
            page.dialog = dlg
            dlg.open = True
            await page.update_async()

        appbar_actions.append(
            ft.TextButton("转办", on_click=_forward, style=ft.ButtonStyle(color=ft.colors.WHITE))
        )

    bottom_bar: ft.Control = ft.Container(visible=False)
    if not is_readonly:
        bottom_bar = ft.Container(
            content=ft.ElevatedButton(
                "提交", on_click=_submit,
                bgcolor=ft.colors.BLUE, color=ft.colors.WHITE, expand=True,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
        )

    body = ft.Column(
        controls=form_controls, spacing=8,
        scroll=ft.ScrollMode.AUTO, expand=True,
    )

    view = ft.View(
        route="/ticket/sign",
        appbar=ft.AppBar(
            title=ft.Text(title),
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE,
            actions=appbar_actions,
        ),
        controls=[body, bottom_bar],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    return view
