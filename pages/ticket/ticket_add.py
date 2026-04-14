"""作业票新增/编辑页 — 参数化表单，根据 ticket_type 渲染不同字段"""

from __future__ import annotations

import asyncio
from typing import Any

import flet as ft

from pages.ticket.config import (
    TICKET_TYPES, FieldDef, get_all_fields, get_config_by_type_value,
)
from services import ticket_service as svc
from utils.app_state import app_state
from components.form_fields import (
    text_field, dropdown_field, radio_field, date_field, form_item,
)


async def build_ticket_add_page(
    page: ft.Page,
    type_value: str,
    sq_id: str = "",
) -> ft.View:
    """构建作业票新增/编辑页。

    参数:
        type_value: 后端类型值 (3/4/5/7/8/10/11/12)
        sq_id: 作业申请 ID（编辑时传入）
    """
    config = get_config_by_type_value(type_value)
    if not config:
        return ft.View(
            route="/ticket/add",
            controls=[ft.Text("未知的作业票类型")],
        )

    all_fields = get_all_fields(config)

    # --- 表单数据 ---
    form_data: dict[str, Any] = {"type": type_value}
    # 设置分析字段默认值
    for f in all_fields:
        if f.widget == "radio" and f.radio_options:
            form_data[f.key] = config.analysis_default

    # --- 数据源 ---
    sources: dict[str, list[dict]] = {
        "departs": [],
        "peoples": [],
        "cameras": [],
        "typeList": [],
        "qttsywbhs": [],
        "peoplesZSs": [],
        "zyjbs": [],
        "zylxs": [],
    }

    # --- 控件引用 ---
    form_column = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
    field_controls: dict[str, ft.Container] = {}  # key -> Container 用于条件显示

    # --- 辅助：扁平化部门树 ---
    def _flatten_departs(tree: dict, result: list):
        if str(tree.get("delFlag", "0")) == "0":
            children = tree.get("children") or []
            if children:
                for child in children:
                    _flatten_departs(child, result)
            else:
                result.append({"id": tree["id"], "text": tree.get("departName", ""), "value": tree["id"]})

    # --- 加载数据源（并行） ---
    async def _load_sources():
        results = await asyncio.gather(
            svc.get_depart_list(),
            svc.get_people_list(),
            svc.get_camera_list(),
            svc.get_dict_work_type(),
            svc.get_qttszyzbh_list(type_value),
            svc.get_dict_items("ticket_zyjb"),
            svc.get_dict_items("mbcd_zylx"),
            svc.get_people_zs_list(type_value),
            return_exceptions=True,
        )
        (depart_result, people_result, camera_result, type_result,
         zbh_result, zyjb_result, zylx_result, zs_result) = results

        # 部门
        if isinstance(depart_result, list) and depart_result:
            flat: list[dict] = []
            _flatten_departs(depart_result[0], flat)
            sources["departs"] = flat

        # 人员
        if isinstance(people_result, dict):
            records = people_result.get("records", [])
            sources["peoples"] = [{"id": r["id"], "text": r.get("xm", ""), "value": r["id"]} for r in records]

        # 摄像头
        if isinstance(camera_result, list):
            sources["cameras"] = [{"id": r["id"], "text": r.get("cameraCode", ""), "value": r["id"]} for r in camera_result]

        # 作业类型列表
        if isinstance(type_result, list):
            sources["typeList"] = [{"text": r.get("text", ""), "value": r.get("value", "")} for r in type_result]

        # 其他特殊作业证编号
        if isinstance(zbh_result, list):
            sources["qttsywbhs"] = [{"text": r.get("text", r.get("zyzbh", "")), "value": r.get("value", r.get("id", ""))} for r in zbh_result]

        # 作业级别字典
        if isinstance(zyjb_result, list):
            sources["zyjbs"] = [{"text": r.get("text", ""), "value": r.get("value", "")} for r in zyjb_result]

        # 盲板作业类别
        if isinstance(zylx_result, list):
            sources["zylxs"] = [{"text": r.get("text", ""), "value": r.get("value", "")} for r in zylx_result]

        # 证书列表
        if isinstance(zs_result, dict):
            records_zs = zs_result.get("records", [])
            sources["peoplesZSs"] = [{"id": r["id"], "text": r.get("xm", ""), "value": r["id"]} for r in records_zs]

    # --- 加载已有数据（编辑模式）---
    async def _load_existing():
        if not sq_id:
            return
        try:
            result = await svc.ticket_detail(config.query_path, sq_id)
            records = result.get("records", []) if isinstance(result, dict) else []
            if records:
                data = records[0]
                for key, val in data.items():
                    if val:
                        form_data[key] = val
        except Exception:
            pass

    # --- 多选弹窗 ---
    async def _show_multi_select(field_key: str, source_key: str, title: str):
        """弹出多选对话框"""
        options = sources.get(source_key, [])
        selected = set(str(form_data.get(field_key, "")).split(",")) if form_data.get(field_key) else set()

        checkboxes: list[ft.Checkbox] = []
        for opt in options:
            cb = ft.Checkbox(
                label=opt["text"],
                value=str(opt["value"]) in selected,
                data=str(opt["value"]),
            )
            checkboxes.append(cb)

        async def _confirm(e):
            vals = [cb.data for cb in checkboxes if cb.value]
            form_data[field_key] = ",".join(vals)
            dlg.open = False
            await page.update_async()
            _refresh_field_display(field_key)
            await page.update_async()

        async def _cancel(e):
            await _close_dlg(dlg)

        dlg = ft.AlertDialog(
            title=ft.Text(title, size=16),
            content=ft.Container(
                content=ft.Column(checkboxes, scroll=ft.ScrollMode.AUTO, tight=True),
                height=400,
                width=300,
            ),
            actions=[
                ft.TextButton("取消", on_click=_cancel),
                ft.ElevatedButton("确定", on_click=_confirm),
            ],
        )
        page.dialog = dlg
        dlg.open = True
        await page.update_async()

    async def _close_dlg(dlg):
        dlg.open = False
        await page.update_async()

    # --- 单选弹窗 ---
    async def _show_single_select(field_key: str, source_key: str, title: str):
        options = sources.get(source_key, [])

        async def _select(val, e):
            form_data[field_key] = val
            dlg.open = False
            await page.update_async()
            _refresh_field_display(field_key)
            await page.update_async()

        def _make_select(v):
            async def _on_click(e):
                await _select(v, e)
            return _on_click

        tiles = []
        for opt in options:
            val = str(opt["value"])
            tiles.append(ft.ListTile(
                title=ft.Text(opt["text"]),
                on_click=_make_select(val),
            ))

        dlg = ft.AlertDialog(
            title=ft.Text(title, size=16),
            content=ft.Container(
                content=ft.Column(tiles, scroll=ft.ScrollMode.AUTO, tight=True),
                height=400,
                width=300,
            ),
        )
        page.dialog = dlg
        dlg.open = True
        await page.update_async()

    # --- 日期选择 ---
    async def _show_date_picker(field_key: str):
        async def _on_date(e):
            if e.control.value:
                import datetime
                dt = e.control.value
                form_data[field_key] = dt.strftime("%Y-%m-%d %H:%M:%S")
                _refresh_field_display(field_key)
                await page.update_async()

        dp = ft.DatePicker(on_change=_on_date)
        page.overlay.append(dp)
        await page.update_async()
        dp.pick_date()

    # --- 刷新字段显示值 ---
    def _refresh_field_display(field_key: str):
        """更新字段显示文本"""
        # 查找对应字段定义
        for f in all_fields:
            if f.key == field_key:
                ctrl_container = field_controls.get(field_key)
                if ctrl_container and hasattr(ctrl_container, '_display_text'):
                    val = form_data.get(field_key, "")
                    if f.widget in ("select_single", "select_multi"):
                        opts = sources.get(f.source, [])
                        vals = str(val).split(",") if val else []
                        names = [o["text"] for o in opts if str(o["value"]) in vals]
                        ctrl_container._display_text.value = ", ".join(names) or "请选择"
                    else:
                        ctrl_container._display_text.value = str(val) or "请选择"
                break

    # --- 条件字段可见性 ---
    def _update_condition_visibility():
        for f in all_fields:
            if f.condition:
                dep_key, dep_val = f.condition
                visible = str(form_data.get(dep_key, "")) == dep_val
                if f.key in field_controls:
                    field_controls[f.key].visible = visible

    # --- 构建单个字段控件 ---
    def _build_field(f: FieldDef) -> ft.Container:
        label_parts: list[ft.Control] = []
        if f.required:
            label_parts.append(ft.Text("*", color=ft.colors.RED, size=14))
        label_parts.append(ft.Text(f.label, size=14, color=ft.colors.GREY_700, width=120))

        if f.widget == "input":
            tf = ft.TextField(
                value=str(form_data.get(f.key, "")),
                hint_text="请填写",
                on_change=lambda e, k=f.key: form_data.__setitem__(k, e.control.value),
                border_color=ft.colors.GREY_300,
                focused_border_color=ft.colors.BLUE,
                content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
                text_size=14,
                expand=True,
            )
            control = tf
        elif f.widget == "number":
            tf = ft.TextField(
                value=str(form_data.get(f.key, "")),
                hint_text="请填写",
                keyboard_type=ft.KeyboardType.NUMBER,
                on_change=lambda e, k=f.key: form_data.__setitem__(k, e.control.value),
                border_color=ft.colors.GREY_300,
                focused_border_color=ft.colors.BLUE,
                content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
                text_size=14,
                expand=True,
            )
            control = tf
        elif f.widget == "radio":
            opts = f.radio_options or []
            rg = ft.RadioGroup(
                value=str(form_data.get(f.key, "")),
                on_change=lambda e, k=f.key: _on_radio_change(k, e),
                content=ft.Row(
                    [ft.Radio(value=o["value"], label=o["text"]) for o in opts],
                    wrap=True,
                ),
            )
            control = rg
        elif f.widget in ("select_single", "select_multi"):
            # 显示已选内容
            val = form_data.get(f.key, "")
            opts = sources.get(f.source, [])
            vals = str(val).split(",") if val else []
            names = [o["text"] for o in opts if str(o["value"]) in vals]
            display = ft.Text(
                ", ".join(names) or "请选择",
                size=14,
                color=ft.colors.GREY_600 if not names else ft.colors.BLACK87,
                expand=True,
            )

            def _make_select_handler(k, s, l, multi):
                async def _on_click(e):
                    if multi:
                        await _show_multi_select(k, s, l)
                    else:
                        await _show_single_select(k, s, l)
                return _on_click

            handler = _make_select_handler(
                f.key, f.source, f.label, f.widget == "select_multi",
            )

            control = ft.Container(
                content=ft.Row(
                    controls=[display, ft.Icon(ft.icons.ARROW_DROP_DOWN, size=20, color=ft.colors.GREY_400)],
                ),
                on_click=handler,
                padding=ft.padding.symmetric(horizontal=10, vertical=10),
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=4,
                expand=True,
                ink=True,
            )
            # 保存引用用于刷新
            control._display_text = display
        elif f.widget == "datetime":
            val = form_data.get(f.key, "")
            display = ft.Text(
                str(val) or "请选择时间",
                size=14,
                color=ft.colors.GREY_600 if not val else ft.colors.BLACK87,
                expand=True,
            )
            def _make_date_handler(k):
                async def _on_click(e):
                    await _show_date_picker(k)
                return _on_click

            control = ft.Container(
                content=ft.Row(
                    controls=[display, ft.Icon(ft.icons.CALENDAR_TODAY, size=20, color=ft.colors.GREY_400)],
                ),
                on_click=_make_date_handler(f.key),
                padding=ft.padding.symmetric(horizontal=10, vertical=10),
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=4,
                expand=True,
                ink=True,
            )
            control._display_text = display
        else:
            control = ft.Text("未知控件类型")

        container = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(controls=label_parts, spacing=2, tight=True),
                    ft.Container(content=control, expand=True),
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            bgcolor=ft.colors.WHITE,
        )

        # 条件字段初始可见性
        if f.condition:
            dep_key, dep_val = f.condition
            container.visible = str(form_data.get(dep_key, "")) == dep_val

        field_controls[f.key] = container
        return container

    def _on_radio_change(key: str, e):
        form_data[key] = e.control.value
        _update_condition_visibility()
        page.update()

    # --- 提交 ---
    async def _submit(save_only: bool = False):
        # 简单必填校验
        missing = []
        for f in all_fields:
            if not f.required:
                continue
            if f.condition:
                dep_key, dep_val = f.condition
                if str(form_data.get(dep_key, "")) != dep_val:
                    continue
            val = form_data.get(f.key, "")
            if not val:
                missing.append(f.label)

        if missing:
            page.snack_bar = ft.SnackBar(
                ft.Text(f"请填写：{', '.join(missing[:3])}{'...' if len(missing) > 3 else ''}"),
                open=True,
            )
            await page.update_async()
            return

        try:
            data = dict(form_data)
            if sq_id:
                data["id"] = sq_id
                await svc.ticket_edit(config.edit_path, data)
            else:
                await svc.ticket_add(config.add_path, data)

            page.snack_bar = ft.SnackBar(
                ft.Text("保存成功" if save_only else "提交成功"), open=True,
            )
            await page.update_async()

            if not save_only:
                page.views.pop()
                await page.update_async()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"提交失败：{ex}"), open=True)
            await page.update_async()

    # --- 组装页面 ---
    # 先加载数据源
    await _load_sources()
    if sq_id:
        await _load_existing()

    # 构建表单字段
    for f in all_fields:
        form_column.controls.append(_build_field(f))

    # 坐标提示
    form_column.controls.insert(
        len(TICKET_TYPES) and 3,  # 在摄像头后面
        ft.Container(
            content=ft.Row([
                ft.Text("*", color=ft.colors.RED, size=14),
                ft.Text("坐标选择", size=14, color=ft.colors.GREY_700, width=120),
                ft.Text("坐标默认为厂区中心，后续需去网页完善！", size=12, color=ft.colors.ORANGE, expand=True),
            ], spacing=2),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            bgcolor=ft.colors.WHITE,
        ),
    )

    async def _on_save(e):
        await _submit(save_only=True)

    async def _on_submit(e):
        await _submit(save_only=False)

    # 底部按钮
    buttons = ft.Container(
        content=ft.Row(
            controls=[
                ft.ElevatedButton(
                    "保存",
                    on_click=_on_save,
                    expand=True,
                ) if sq_id else ft.Container(),
                ft.ElevatedButton(
                    "提交",
                    on_click=_on_submit,
                    bgcolor=ft.colors.BLUE,
                    color=ft.colors.WHITE,
                    expand=True,
                ),
            ],
            spacing=12,
        ),
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
        bgcolor=ft.colors.WHITE,
    )

    view = ft.View(
        route="/ticket/add",
        appbar=ft.AppBar(
            title=ft.Text(f"新增{config.name}"),
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE,
        ),
        controls=[form_column, buttons],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    return view
