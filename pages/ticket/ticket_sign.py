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
from utils.app_state import app_state
from components.sign_pad import SignPad
from components.form_fields import textarea_field, radio_field


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
    """构建作业票签名页。

    参数:
        mode: 签名模式 (confess/assessment/assessment_other/approve/acceptance)
        info_json: JSON 编码的签名信息
        type_value: 作业票类型值
    """
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

    # --- 状态 ---
    form_data: dict[str, Any] = {
        "opinion": info.get("opinion", ""),
        "signArea": info.get("signArea", ""),
        "photo": info.get("photo", ""),
        "selected": info.get("selected", ""),
        "aqcs": info.get("aqcs", ""),
        "applyStatus": info.get("applyStatus", ""),
    }
    sign_image_path = [""]

    title = _MODE_TITLES.get(mode, "签名")

    # --- 签名回调 ---
    async def _on_sign_success(file_path: str):
        sign_image_path[0] = file_path
        form_data["signArea"] = file_path

    sign_pad = SignPad(
        page,
        on_success=_on_sign_success,
        sign_image=info.get("signArea", ""),
        disabled=is_readonly,
    )

    # --- 构建表单 ---
    form_controls: list[ft.Control] = []

    if mode == "confess":
        # 安全交底：意见 + 签名 + 照片
        opinion_field = ft.TextField(
            value=form_data["opinion"],
            hint_text="请输入交底内容",
            multiline=True,
            min_lines=3,
            max_lines=6,
            on_change=lambda e: form_data.__setitem__("opinion", e.control.value),
            read_only=is_readonly,
            border_color=ft.colors.GREY_300,
            text_size=14,
        )
        form_controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("交底内容", size=14, weight=ft.FontWeight.W_500),
                    opinion_field,
                ], spacing=8),
                padding=16,
                bgcolor=ft.colors.WHITE,
            )
        )

    elif mode == "assessment":
        # 安全措施：措施内容 + 是否涉及 + 签名
        form_controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("安全措施", size=14, weight=ft.FontWeight.W_500),
                    ft.Text(form_data.get("aqcs", ""), size=13, color=ft.colors.GREY_700),
                ], spacing=8),
                padding=16,
                bgcolor=ft.colors.WHITE,
            )
        )

        # 是否涉及
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
                    padding=16,
                    bgcolor=ft.colors.WHITE,
                )
            )

    elif mode == "assessment_other":
        # 其他安全措施：措施内容 + 是否涉及 + 双签名
        form_controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("其他安全措施", size=14, weight=ft.FontWeight.W_500),
                    ft.TextField(
                        value=form_data.get("aqcs", ""),
                        hint_text="请输入安全措施",
                        multiline=True,
                        min_lines=3,
                        on_change=lambda e: form_data.__setitem__("aqcs", e.control.value),
                        read_only=is_readonly,
                        border_color=ft.colors.GREY_300,
                        text_size=14,
                    ),
                ], spacing=8),
                padding=16,
                bgcolor=ft.colors.WHITE,
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
                    padding=16,
                    bgcolor=ft.colors.WHITE,
                )
            )

    elif mode == "approve":
        # 审批：意见 + 审批结果 + 签名 + 照片
        opinion_field = ft.TextField(
            value=form_data["opinion"],
            hint_text="请输入审批意见",
            multiline=True,
            min_lines=3,
            max_lines=6,
            on_change=lambda e: form_data.__setitem__("opinion", e.control.value),
            read_only=is_readonly,
            border_color=ft.colors.GREY_300,
            text_size=14,
        )
        form_controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("审批意见", size=14, weight=ft.FontWeight.W_500),
                    opinion_field,
                ], spacing=8),
                padding=16,
                bgcolor=ft.colors.WHITE,
            )
        )

        # 审批结果（加载字典）
        apply_status_options: list[dict] = []
        try:
            status_result = await svc.get_dict_apply_status(config.api_prefix)
            if isinstance(status_result, list):
                apply_status_options = [{"text": r.get("text", ""), "value": r.get("value", "")} for r in status_result]
        except Exception:
            apply_status_options = [{"text": "同意", "value": "1"}, {"text": "不同意", "value": "2"}]

        if not is_readonly:
            rg = ft.RadioGroup(
                value=form_data.get("applyStatus", ""),
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
                        rg,
                    ], spacing=8),
                    padding=16,
                    bgcolor=ft.colors.WHITE,
                )
            )

    elif mode == "acceptance":
        # 验收：提示 + 意见 + 签名 + 照片
        form_controls.append(
            ft.Container(
                content=ft.Text(
                    "本许可证工作执行完毕，现场处于安全、清洁状态",
                    size=13, color=ft.colors.BLUE_700, italic=True,
                ),
                padding=16,
                bgcolor=ft.colors.BLUE_50,
                border_radius=8,
                margin=ft.margin.symmetric(horizontal=0, vertical=4),
            )
        )
        opinion_field = ft.TextField(
            value=form_data["opinion"],
            hint_text="请输入验收意见",
            multiline=True,
            min_lines=3,
            max_lines=6,
            on_change=lambda e: form_data.__setitem__("opinion", e.control.value),
            read_only=is_readonly,
            border_color=ft.colors.GREY_300,
            text_size=14,
        )
        form_controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("验收意见", size=14, weight=ft.FontWeight.W_500),
                    opinion_field,
                ], spacing=8),
                padding=16,
                bgcolor=ft.colors.WHITE,
            )
        )

    # --- 签名区域 ---
    form_controls.append(
        ft.Container(
            content=ft.Column([
                ft.Text("签名", size=14, weight=ft.FontWeight.W_500),
                sign_pad,
            ], spacing=8),
            padding=16,
            bgcolor=ft.colors.WHITE,
        )
    )

    # --- 提交按钮 ---
    async def _submit(e):
        # 校验签名
        if not form_data.get("signArea") and not sign_image_path[0]:
            page.snack_bar = ft.SnackBar(ft.Text("请先签名"), open=True)
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
                params["aqcs"] = form_data.get("aqcs", "")
                await svc.measures_apply(config.api_prefix, params)

            elif mode == "approve":
                if not form_data.get("applyStatus"):
                    page.snack_bar = ft.SnackBar(ft.Text("请选择审批结果"), open=True)
                    await page.update_async()
                    return
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
            # 返回上一页
            if len(page.views) > 1:
                page.views.pop()
                await page.update_async()

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"提交失败：{ex}"), open=True)
            await page.update_async()

    # 转办按钮（仅审批模式）
    appbar_actions = []
    if mode == "approve" and not is_readonly:
        async def _forward(e):
            try:
                people = await svc.get_people_list_for_forward(config.api_prefix)
                people_list = people if isinstance(people, list) else []
            except Exception:
                people_list = []

            async def _do_forward(person_id, dlg):
                try:
                    await svc.forward_approve(config.api_prefix, {"id": item_id, "person": person_id})
                    dlg.open = False
                    page.snack_bar = ft.SnackBar(ft.Text("转办成功"), open=True)
                    await page.update_async()
                    if len(page.views) > 1:
                        page.views.pop()
                        await page.update_async()
                except Exception as ex:
                    page.snack_bar = ft.SnackBar(ft.Text(f"转办失败：{ex}"), open=True)
                    await page.update_async()

            tiles = [
                ft.ListTile(
                    title=ft.Text(p.get("name", p.get("realname", ""))),
                    on_click=lambda e, pid=p.get("id", ""): _do_forward(pid, dlg),
                )
                for p in people_list
            ]
            dlg = ft.AlertDialog(
                title=ft.Text("选择转办人"),
                content=ft.Container(
                    content=ft.Column(tiles, scroll=ft.ScrollMode.AUTO, tight=True),
                    height=400, width=300,
                ),
            )
            page.dialog = dlg
            dlg.open = True
            await page.update_async()

        appbar_actions.append(
            ft.TextButton("转办", on_click=_forward, style=ft.ButtonStyle(color=ft.colors.WHITE))
        )

    # --- 底部按钮 ---
    bottom_bar = ft.Container(visible=not is_readonly)
    if not is_readonly:
        bottom_bar = ft.Container(
            content=ft.ElevatedButton(
                "提交",
                on_click=_submit,
                bgcolor=ft.colors.BLUE,
                color=ft.colors.WHITE,
                expand=True,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
        )

    # --- 组装 ---
    body = ft.Column(
        controls=form_controls,
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
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
