"""作业票新增/编辑页 — 参数化表单，根据 ticket_type 渲染不同字段"""

from __future__ import annotations

import asyncio
import calendar
import datetime
import json as _json
from typing import Any

import flet as ft

from pages.ticket.config import (
    TICKET_TYPES, FieldDef, get_all_fields, get_config_by_type_value,
)
from services import ticket_service as svc
from utils.app_state import app_state
from utils.geo import get_phone_location
from utils.logger import get_logger

log = get_logger("ticket_add")

# 默认坐标（厂区中心）— 与 uniapp 原版的兜底值一致
DEFAULT_COORD = {"lng": 120.0, "lat": 30.0}


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
    for f in all_fields:
        if f.widget == "radio" and f.radio_options:
            form_data[f.key] = config.analysis_default

    # --- 数据源 ---
    sources: dict[str, list[dict]] = {
        "departs": [],
        "peoples": [],
        "peoplesZS": [],   # 作业人（有证书人员列表）
        "peoplesZSs": [],  # 动火人证书编号（基于作业人动态加载）
        "cameras": [],
        "typeList": [],
        "qttsywbhs": [],
        "zyjbs": [],
        "zylxs": [],
    }

    # 加载状态
    loading_spinner = ft.Container(
        content=ft.Column(
            [
                ft.ProgressRing(width=32, height=32),
                ft.Text("加载中...", size=13, color=ft.colors.GREY_500),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
        alignment=ft.alignment.center,
        expand=True,
    )

    form_column = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
    field_controls: dict[str, ft.Container] = {}

    # 坐标状态：优先手机定位；失败则走 uniapp 的厂区中心 fallback
    # 未取到前 resolved=False，提交时阻止
    coord_state: dict[str, Any] = {
        "lng": None,
        "lat": None,
        "source": "",       # gps | factory | manual
        "resolved": False,
    }

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
        zyjb_dict = config.zyjb_dict or "ticket_zyjb"
        results = await asyncio.gather(
            svc.get_depart_list(),
            svc.get_people_list(),
            svc.get_camera_list(),
            svc.get_dict_work_type(),
            svc.get_dict_items(zyjb_dict),
            svc.get_dict_items("mbcd_zylx"),
            svc.get_people_zs_list(type_value),
            return_exceptions=True,
        )
        (depart_result, people_result, camera_result, type_result,
         zyjb_result, zylx_result, zs_result) = results

        if isinstance(depart_result, list) and depart_result:
            flat: list[dict] = []
            _flatten_departs(depart_result[0], flat)
            sources["departs"] = flat

        if isinstance(people_result, dict):
            records = people_result.get("records", [])
            sources["peoples"] = [
                {"id": r["id"], "text": r.get("xm", ""), "value": r["id"]}
                for r in records
            ]

        if isinstance(camera_result, list):
            sources["cameras"] = [
                {"id": r["id"], "text": r.get("cameraCode", ""), "value": r["id"]}
                for r in camera_result
            ]

        if isinstance(type_result, list):
            sources["typeList"] = [
                {"text": r.get("text", ""), "value": r.get("value", "")}
                for r in type_result
            ]

        if isinstance(zyjb_result, list):
            sources["zyjbs"] = [
                {"text": r.get("text", ""), "value": r.get("value", "")}
                for r in zyjb_result
            ]

        if isinstance(zylx_result, list):
            sources["zylxs"] = [
                {"text": r.get("text", ""), "value": r.get("value", "")}
                for r in zylx_result
            ]

        if isinstance(zs_result, dict):
            records_zs = zs_result.get("records", [])
            sources["peoplesZS"] = [
                {"id": r["id"], "text": r.get("xm", ""), "value": r["id"]}
                for r in records_zs
            ]

    # --- 根据作业人 ID 加载证书编号列表 ---
    async def _reload_people_zss():
        ids = form_data.get("zyr", "")
        if not ids:
            sources["peoplesZSs"] = []
            return
        try:
            result = await svc.get_user_zs(type_value, ids)
            if isinstance(result, list):
                sources["peoplesZSs"] = [
                    {
                        "id": r.get("zsId", ""),
                        "text": r.get("zs", ""),
                        "value": r.get("zsId", ""),
                    }
                    for r in result
                ]
            else:
                sources["peoplesZSs"] = []
        except Exception:
            sources["peoplesZSs"] = []

    # --- 根据"涉及的其他特殊作业"加载证编号 ---
    async def _reload_qttsywbhs():
        zylb = form_data.get("sjdqttszy", "")
        if not zylb:
            sources["qttsywbhs"] = []
            return
        try:
            result = await svc.get_qttszyzbh_list(zylb)
            if isinstance(result, list):
                sources["qttsywbhs"] = [
                    {
                        "id": r.get("text", ""),
                        "text": r.get("text", ""),
                        "value": r.get("text", ""),
                    }
                    for r in result
                ]
            else:
                sources["qttsywbhs"] = []
        except Exception:
            sources["qttsywbhs"] = []

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
                # 从坐标字段反解经纬度，编辑模式直接复用已有坐标
                coord_field = config.coord_field or "zb"
                raw = data.get(coord_field)
                if raw:
                    try:
                        zb = _json.loads(raw) if isinstance(raw, str) else raw
                        loc = (zb.get("locations") or [{}])[0]
                        if loc.get("lng") is not None and loc.get("lat") is not None:
                            coord_state["lng"] = float(loc["lng"])
                            coord_state["lat"] = float(loc["lat"])
                            coord_state["source"] = "existing"
                            coord_state["resolved"] = True
                    except (ValueError, TypeError, AttributeError):
                        log.exception("parse existing coord failed")
                # 编辑模式：同步加载动态数据源
                await _reload_people_zss()
                await _reload_qttsywbhs()
        except Exception:
            log.exception("load existing ticket failed")

    # --- 字段联动：选中确认后触发 ---
    async def _on_field_change(field_key: str):
        if field_key == "zyr":
            form_data["dhzsbh"] = ""
            await _reload_people_zss()
            _refresh_field_display("dhzsbh")
        elif field_key == "sjdqttszy":
            tail_key = "qttsywbh" if config.code == "DH" else "sjdqttszyaqzyzbh"
            form_data[tail_key] = ""
            await _reload_qttsywbhs()
            _refresh_field_display(tail_key)

    # --- 多选弹窗（带搜索） ---
    async def _show_multi_select(field_key: str, source_key: str, title: str):
        options = sources.get(source_key, [])
        selected: set[str] = set(
            s for s in str(form_data.get(field_key, "")).split(",") if s
        )

        list_column_inner = ft.Column(scroll=ft.ScrollMode.AUTO, tight=True, spacing=0)

        def _make_on_cb(val: str):
            def _on(e):
                if e.control.value:
                    selected.add(val)
                else:
                    selected.discard(val)
            return _on

        def _rebuild(query: str = ""):
            list_column_inner.controls.clear()
            q = (query or "").strip()
            for opt in options:
                label = str(opt.get("text", ""))
                if q and q not in label:
                    continue
                val = str(opt.get("value", ""))
                list_column_inner.controls.append(
                    ft.Checkbox(
                        label=label,
                        value=val in selected,
                        data=val,
                        on_change=_make_on_cb(val),
                    )
                )
            if not list_column_inner.controls:
                list_column_inner.controls.append(
                    ft.Container(
                        content=ft.Text("无匹配项", color=ft.colors.GREY_500, size=13),
                        padding=10,
                        alignment=ft.alignment.center,
                    )
                )

        async def _on_search(e):
            _rebuild(search_tf.value or "")
            await page.update_async()

        search_tf = ft.TextField(
            hint_text="搜索",
            prefix_icon=ft.icons.SEARCH,
            on_change=_on_search,
            dense=True,
            height=40,
            text_size=13,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
        )
        _rebuild()

        async def _confirm(e):
            form_data[field_key] = ",".join(sorted(selected))
            page.close(dlg)
            _refresh_field_display(field_key)
            await _on_field_change(field_key)
            await page.update_async()

        async def _cancel(e):
            page.close(dlg)

        async def _clear(e):
            selected.clear()
            _rebuild(search_tf.value or "")
            await page.update_async()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(title, size=16),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        search_tf,
                        ft.Container(
                            content=list_column_inner,
                            height=360,
                            border=ft.border.all(1, ft.colors.GREY_200),
                            border_radius=4,
                        ),
                    ],
                    tight=True,
                    spacing=8,
                ),
                width=320,
            ),
            actions=[
                ft.TextButton("清空", on_click=_clear),
                ft.TextButton("取消", on_click=_cancel),
                ft.ElevatedButton("确定", on_click=_confirm),
            ],
        )
        page.open(dlg)

    # --- 单选弹窗（带搜索） ---
    async def _show_single_select(field_key: str, source_key: str, title: str):
        options = sources.get(source_key, [])
        current = str(form_data.get(field_key, ""))
        state: dict[str, str] = {"val": current}

        list_column_inner = ft.Column(scroll=ft.ScrollMode.AUTO, tight=True, spacing=0)

        def _make_on_click(val: str):
            async def _on(e):
                state["val"] = val
                _rebuild(search_tf.value or "")
                await page.update_async()
            return _on

        def _rebuild(query: str = ""):
            list_column_inner.controls.clear()
            q = (query or "").strip()
            for opt in options:
                label = str(opt.get("text", ""))
                if q and q not in label:
                    continue
                val = str(opt.get("value", ""))
                is_sel = val == state["val"]
                list_column_inner.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(
                                ft.icons.RADIO_BUTTON_CHECKED if is_sel else ft.icons.RADIO_BUTTON_UNCHECKED,
                                size=18,
                                color=ft.colors.BLUE if is_sel else ft.colors.GREY_400,
                            ),
                            ft.Text(label, size=14),
                        ]),
                        on_click=_make_on_click(val),
                        padding=ft.padding.symmetric(horizontal=10, vertical=8),
                        ink=True,
                    )
                )
            if not list_column_inner.controls:
                list_column_inner.controls.append(
                    ft.Container(
                        content=ft.Text("无匹配项", color=ft.colors.GREY_500, size=13),
                        padding=10,
                        alignment=ft.alignment.center,
                    )
                )

        async def _on_search(e):
            _rebuild(search_tf.value or "")
            await page.update_async()

        search_tf = ft.TextField(
            hint_text="搜索",
            prefix_icon=ft.icons.SEARCH,
            on_change=_on_search,
            dense=True,
            height=40,
            text_size=13,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
        )
        _rebuild()

        async def _confirm(e):
            form_data[field_key] = state["val"]
            page.close(dlg)
            _refresh_field_display(field_key)
            await _on_field_change(field_key)
            await page.update_async()

        async def _cancel(e):
            page.close(dlg)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(title, size=16),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        search_tf,
                        ft.Container(
                            content=list_column_inner,
                            height=360,
                            border=ft.border.all(1, ft.colors.GREY_200),
                            border_radius=4,
                        ),
                    ],
                    tight=True,
                    spacing=8,
                ),
                width=320,
            ),
            actions=[
                ft.TextButton("取消", on_click=_cancel),
                ft.ElevatedButton("确定", on_click=_confirm),
            ],
        )
        page.open(dlg)

    # --- 中文日期时间选择（年/月/日/时/分/秒） ---
    async def _show_datetime_picker(field_key: str):
        now = datetime.datetime.now()
        cur = str(form_data.get(field_key, ""))
        dt = now
        if cur:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    dt = datetime.datetime.strptime(cur, fmt)
                    break
                except ValueError:
                    continue

        def _dd(vals: list[str], value: str, width: int) -> ft.Dropdown:
            return ft.Dropdown(
                value=value,
                options=[ft.dropdown.Option(v) for v in vals],
                width=width,
                dense=True,
                text_size=13,
                content_padding=ft.padding.symmetric(horizontal=6, vertical=4),
            )

        years = [str(y) for y in range(now.year - 5, now.year + 10)]
        months = [f"{m:02d}" for m in range(1, 13)]
        hours = [f"{h:02d}" for h in range(0, 24)]
        mins = [f"{m:02d}" for m in range(0, 60)]
        secs = [f"{s:02d}" for s in range(0, 60)]

        def _days_in(year: int, month: int) -> list[str]:
            return [f"{d:02d}" for d in range(1, calendar.monthrange(year, month)[1] + 1)]

        year_dd = _dd(years, str(dt.year), 90)
        month_dd = _dd(months, f"{dt.month:02d}", 70)
        day_dd = _dd(_days_in(dt.year, dt.month), f"{dt.day:02d}", 70)
        hour_dd = _dd(hours, f"{dt.hour:02d}", 70)
        min_dd = _dd(mins, f"{dt.minute:02d}", 70)
        sec_dd = _dd(secs, f"{dt.second:02d}", 70)

        async def _on_ym_change(e):
            """年/月变化时重算天数，防止非法日期（如 2 月 31 日）"""
            try:
                y = int(year_dd.value or dt.year)
                m = int(month_dd.value or dt.month)
            except ValueError:
                return
            valid = _days_in(y, m)
            day_dd.options = [ft.dropdown.Option(v) for v in valid]
            if day_dd.value not in valid:
                day_dd.value = valid[-1]
            await page.update_async()

        year_dd.on_change = _on_ym_change
        month_dd.on_change = _on_ym_change

        def _label(txt: str):
            return ft.Text(txt, size=13, color=ft.colors.GREY_700)

        async def _confirm(e):
            val = (
                f"{year_dd.value}-{month_dd.value}-{day_dd.value} "
                f"{hour_dd.value}:{min_dd.value}:{sec_dd.value}"
            )
            form_data[field_key] = val
            page.close(dlg)
            _refresh_field_display(field_key)
            await page.update_async()

        async def _cancel(e):
            page.close(dlg)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("选择时间", size=16),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([year_dd, _label("年"), month_dd, _label("月"), day_dd, _label("日")],
                           alignment=ft.MainAxisAlignment.START, spacing=4),
                    ft.Row([hour_dd, _label("时"), min_dd, _label("分"), sec_dd, _label("秒")],
                           alignment=ft.MainAxisAlignment.START, spacing=4),
                ], tight=True, spacing=12),
                width=360,
            ),
            actions=[
                ft.TextButton("取消", on_click=_cancel),
                ft.ElevatedButton("确定", on_click=_confirm),
            ],
        )
        page.open(dlg)

    # --- 刷新字段显示值 ---
    def _refresh_field_display(field_key: str):
        for f in all_fields:
            if f.key != field_key:
                continue
            ctrl_container = field_controls.get(field_key)
            if not ctrl_container:
                return
            display = getattr(ctrl_container, "_display_text", None)
            if display is None:
                return
            val = form_data.get(field_key, "")
            if f.widget in ("select_single", "select_multi"):
                opts = sources.get(f.source, [])
                vals = [v for v in str(val).split(",") if v]
                names = [o["text"] for o in opts if str(o["value"]) in vals]
                display.value = ", ".join(names) if names else "请选择"
                display.color = ft.colors.BLACK87 if names else ft.colors.GREY_600
            else:
                display.value = str(val) if val else "请选择时间"
                display.color = ft.colors.BLACK87 if val else ft.colors.GREY_600
            return

    # --- 条件字段可见性 ---
    def _update_condition_visibility():
        for f in all_fields:
            if not f.condition:
                continue
            dep_key, dep_val = f.condition
            visible = str(form_data.get(dep_key, "")) == dep_val
            if f.key in field_controls:
                field_controls[f.key].visible = visible

    # --- 构建单个字段控件 ---
    def _build_field(f: FieldDef) -> ft.Container:
        label_parts: list[ft.Control] = []
        if f.required:
            label_parts.append(ft.Text("*", color=ft.colors.RED, size=14))
        label_parts.append(ft.Text(f.label, size=14, color=ft.colors.GREY_700, width=140))

        display_ref: ft.Text | None = None

        if f.widget == "input":
            control = ft.TextField(
                value=str(form_data.get(f.key, "")),
                hint_text="请填写",
                on_change=lambda e, k=f.key: form_data.__setitem__(k, e.control.value),
                border_color=ft.colors.GREY_300,
                focused_border_color=ft.colors.BLUE,
                content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
                text_size=14,
                expand=True,
            )
        elif f.widget == "number":
            control = ft.TextField(
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
        elif f.widget == "radio":
            opts = f.radio_options or []
            control = ft.RadioGroup(
                value=str(form_data.get(f.key, "")),
                on_change=lambda e, k=f.key: _on_radio_change(k, e),
                content=ft.Row(
                    [ft.Radio(value=o["value"], label=o["text"]) for o in opts],
                    wrap=True,
                ),
            )
        elif f.widget in ("select_single", "select_multi"):
            val = form_data.get(f.key, "")
            opts = sources.get(f.source, [])
            vals = [v for v in str(val).split(",") if v]
            names = [o["text"] for o in opts if str(o["value"]) in vals]
            display_ref = ft.Text(
                ", ".join(names) if names else "请选择",
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
                    controls=[display_ref, ft.Icon(ft.icons.ARROW_DROP_DOWN, size=20, color=ft.colors.GREY_400)],
                ),
                on_click=handler,
                padding=ft.padding.symmetric(horizontal=10, vertical=10),
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=4,
                expand=True,
                ink=True,
            )
        elif f.widget == "datetime":
            val = form_data.get(f.key, "")
            display_ref = ft.Text(
                str(val) if val else "请选择时间",
                size=14,
                color=ft.colors.GREY_600 if not val else ft.colors.BLACK87,
                expand=True,
            )

            def _make_date_handler(k):
                async def _on_click(e):
                    await _show_datetime_picker(k)
                return _on_click

            control = ft.Container(
                content=ft.Row(
                    controls=[display_ref, ft.Icon(ft.icons.CALENDAR_TODAY, size=20, color=ft.colors.GREY_400)],
                ),
                on_click=_make_date_handler(f.key),
                padding=ft.padding.symmetric(horizontal=10, vertical=10),
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=4,
                expand=True,
                ink=True,
            )
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

        # 将 display Text 引用挂到 container，供 _refresh_field_display 使用
        if display_ref is not None:
            container._display_text = display_ref

        if f.condition:
            dep_key, dep_val = f.condition
            container.visible = str(form_data.get(dep_key, "")) == dep_val

        field_controls[f.key] = container
        return container

    def _on_radio_change(key: str, e):
        form_data[key] = e.control.value
        _update_condition_visibility()
        # 使用 run_task 避免在 sync 回调中调用 async update 导致死锁
        page.run_task(page.update_async)

    # --- 构造坐标 JSON ---
    def _build_coord_json() -> str | None:
        """打包后端要求的 JSON；坐标未获取到返回 None"""
        lng = coord_state.get("lng")
        lat = coord_state.get("lat")
        if lng is None or lat is None:
            return None
        try:
            lng_f = float(lng)
            lat_f = float(lat)
        except (TypeError, ValueError):
            return None
        org_code = app_state.user_info.get("orgCode") or "A01A01"
        return _json.dumps({
            "sysOrgCode": org_code,
            "height": "2",
            "locations": [{"lng": lng_f, "lat": lat_f}],
        })

    # --- 提交 ---
    async def _submit(save_only: bool = False):
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
            page.open(ft.SnackBar(
                ft.Text(f"请填写：{', '.join(missing[:3])}{'...' if len(missing) > 3 else ''}"),
            ))
            return

        # 坐标校验：必须已解析出经纬度（GPS 或 厂区中心 fallback）
        coord_field = config.coord_field or "zb"
        if not coord_state.get("resolved"):
            page.open(ft.SnackBar(ft.Text("定位尚未完成，请稍候或点击重新定位")))
            return
        coord_json = _build_coord_json()
        if coord_json is None:
            page.open(ft.SnackBar(ft.Text("坐标无效，请重新定位")))
            return

        try:
            data = dict(form_data)
            if not data.get(coord_field):
                data[coord_field] = coord_json

            if sq_id:
                data["id"] = sq_id
                await svc.ticket_edit(config.edit_path, data)
            else:
                await svc.ticket_add(config.add_path, data)

            page.open(ft.SnackBar(ft.Text("保存成功" if save_only else "提交成功")))

            # 首页待办/红点可能变化，清 tab 缓存
            invalidator = getattr(app_state, "invalidate_tab_cache", None)
            if callable(invalidator):
                invalidator()

            if not save_only:
                page.views.pop()
                await page.update_async()
        except Exception as ex:
            log.exception("submit ticket failed")
            page.open(ft.SnackBar(ft.Text(f"提交失败：{ex}")))

    # --- 组装页面 ---
    # 先显示加载中
    form_column.controls.append(loading_spinner)

    async def _on_save(e):
        await _submit(save_only=True)

    async def _on_submit(e):
        await _submit(save_only=False)

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

    # --- 坐标显示行：单字段 + 定位状态 + 手动刷新 ---
    coord_display = ft.Text(
        "正在获取手机定位...",
        size=14,
        color=ft.colors.GREY_600,
        expand=True,
    )
    coord_source_hint = ft.Text("", size=11, color=ft.colors.GREY_500)
    coord_progress = ft.ProgressRing(width=16, height=16, stroke_width=2, visible=True)
    coord_refresh_btn = ft.TextButton("重新定位", visible=False)

    def _render_coord():
        if coord_state["resolved"]:
            lng = coord_state["lng"]
            lat = coord_state["lat"]
            coord_display.value = f"{lng:.6f}, {lat:.6f}"
            coord_display.color = ft.colors.BLACK87
            src = coord_state["source"]
            coord_source_hint.value = {
                "gps": "手机 GPS",
                "factory": "厂区中心（GPS 不可用）",
                "existing": "已保存坐标",
                "manual": "手动输入",
            }.get(src, "")
        else:
            coord_display.value = "正在获取手机定位..."
            coord_display.color = ft.colors.GREY_600
            coord_source_hint.value = ""
        coord_progress.visible = not coord_state["resolved"]
        coord_refresh_btn.visible = coord_state["resolved"]

    async def _resolve_coord():
        # 1) 先尝试手机 GPS（最多等 6s）
        coord_state["resolved"] = False
        _render_coord()
        await _safe_update()

        gps = await get_phone_location(page, timeout=6.0)
        if gps is not None:
            lng, lat = gps
            coord_state.update({"lng": lng, "lat": lat, "source": "gps", "resolved": True})
            _render_coord()
            await _safe_update()
            return

        # 2) 兜底：uniapp 的厂区中心坐标
        fallback = None
        try:
            fallback = await svc.get_factory_center_coord()
        except Exception:
            log.exception("factory center coord failed")
        if fallback is not None:
            lng, lat = fallback
            coord_state.update({"lng": lng, "lat": lat, "source": "factory", "resolved": True})
        else:
            lng = float(DEFAULT_COORD["lng"])
            lat = float(DEFAULT_COORD["lat"])
            coord_state.update({"lng": lng, "lat": lat, "source": "factory", "resolved": True})
            page.open(ft.SnackBar(ft.Text("未获取到定位，已使用默认坐标")))
        _render_coord()
        await _safe_update()

    async def _safe_update():
        try:
            await page.update_async()
        except Exception:
            log.debug("swallowed exception", exc_info=True)

    async def _on_refresh_coord(_e):
        await _resolve_coord()

    coord_refresh_btn.on_click = _on_refresh_coord

    def _build_coord_row() -> ft.Container:
        _render_coord()
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("*", color=ft.colors.RED, size=14),
                            ft.Text("坐标", size=14, color=ft.colors.GREY_700, width=140),
                        ],
                        spacing=2, tight=True,
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[coord_progress, coord_display, coord_refresh_btn],
                                    spacing=8,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                coord_source_hint,
                            ],
                            spacing=2,
                            tight=True,
                        ),
                        expand=True,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            bgcolor=ft.colors.WHITE,
        )

    # 后台加载数据 + 渲染表单
    async def _deferred_init():
        try:
            await _load_sources()
            if sq_id:
                await _load_existing()

            form_column.controls.clear()
            for f in all_fields:
                form_column.controls.append(_build_field(f))
            form_column.controls.append(_build_coord_row())
        except Exception as ex:
            log.exception("ticket add init failed")
            form_column.controls.clear()
            form_column.controls.append(
                ft.Container(
                    content=ft.Text(f"加载失败：{ex}", color=ft.colors.RED, size=14),
                    padding=16,
                    alignment=ft.alignment.center,
                )
            )

        await _safe_update()

        # 编辑模式已有坐标则跳过定位，否则自动拉取手机 GPS
        if not coord_state.get("resolved"):
            await _resolve_coord()

    page.run_task(_deferred_init)

    return view
