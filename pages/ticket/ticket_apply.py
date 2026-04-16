"""作业申请列表页 — 对应原 jobTicketSq/zysq.vue"""

from __future__ import annotations

import datetime
from typing import Any

import flet as ft

from components.scroll_helper import apply_no_bounce

from services import ticket_service as svc
from utils.logger import get_logger
from utils.ui import cleanup_overlays, close_and_remove

log = get_logger("ticket_apply")


_TYPE_NAMES = {
    "3": "动火作业", "4": "受限空间作业", "5": "高处作业",
    "7": "吊装作业", "8": "临时用电作业", "10": "盲板抽堵作业",
    "11": "断路作业", "12": "动土作业",
}

_STATUS_MAP = {
    "0": ("待审核", ft.colors.ORANGE),
    "1": ("审核中", ft.colors.BLUE),
    "2": ("已审核", ft.colors.GREEN),
}


async def build_ticket_apply_page(page: ft.Page) -> ft.View:
    page_no = [1]
    page_size = 10
    items_data: list[dict] = []
    is_loading = [False]

    type_options: list[dict] = []
    departs: list[dict] = []
    peoples: list[dict] = []

    list_column = ft.Column(spacing=0, expand=True)
    loading_ring = ft.ProgressRing(width=24, height=24, visible=False)
    load_more_btn = ft.Container(visible=False)
    empty_widget = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.icons.INBOX_OUTLINED, size=64, color=ft.colors.GREY_300),
                ft.Text("暂无数据", size=14, color=ft.colors.GREY_400),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        alignment=ft.alignment.center,
        padding=ft.padding.only(top=120),
        visible=False,
    )

    def _flatten_departs(tree: dict, result: list):
        if str(tree.get("delFlag", "0")) == "0":
            children = tree.get("children") or []
            if children:
                for child in children:
                    _flatten_departs(child, result)
            else:
                result.append({"id": tree["id"], "text": tree.get("departName", ""), "value": tree["id"]})

    async def _init_sources():
        nonlocal type_options, departs, peoples
        try:
            type_result = await svc.get_dict_work_type()
            if isinstance(type_result, list):
                type_options = [{"text": r.get("text", ""), "value": r.get("value", "")} for r in type_result]
        except Exception:
            log.debug("swallowed exception", exc_info=True)

        try:
            depart_result = await svc.get_depart_list()
            flat: list[dict] = []
            if isinstance(depart_result, list) and depart_result:
                _flatten_departs(depart_result[0], flat)
            departs = flat
        except Exception:
            log.debug("swallowed exception", exc_info=True)

        try:
            people_result = await svc.get_people_list()
            records = people_result.get("records", []) if isinstance(people_result, dict) else []
            peoples = [{"id": r["id"], "text": r.get("xm", ""), "value": r["id"]} for r in records]
        except Exception:
            log.debug("swallowed exception", exc_info=True)

    async def _load(reset: bool = False):
        if is_loading[0]:
            return
        is_loading[0] = True
        loading_ring.visible = True
        await page.update_async()

        if reset:
            page_no[0] = 1
            items_data.clear()
            list_column.controls.clear()

        try:
            result = await svc.zysq_list({
                "pageNo": page_no[0],
                "pageSize": page_size,
                "column": "createTime",
                "order": "desc",
            })
            records = result.get("records", []) if isinstance(result, dict) else []
            total = result.get("total", 0) if isinstance(result, dict) else 0

            for item in records:
                items_data.append(item)
                list_column.controls.append(_build_item(item))

            load_more_btn.visible = len(items_data) < total
            load_more_btn.content = ft.TextButton("加载更多", on_click=_on_load_more)
            empty_widget.visible = len(items_data) == 0

        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"加载失败：{ex}")))

        is_loading[0] = False
        loading_ring.visible = False
        await page.update_async()

    async def _on_load_more(e):
        page_no[0] += 1
        await _load(reset=False)

    def _build_item(item: dict) -> ft.Control:
        sq_status = str(item.get("sqStatus", "0"))
        status_text, status_color = _STATUS_MAP.get(sq_status, ("未知", ft.colors.GREY))
        type_name = _TYPE_NAMES.get(str(item.get("zylx", "")), "")

        async def _on_edit(e, it=item):
            await _show_form(it)

        async def _on_apply(e, it=item):
            await _change_status(it["id"])

        async def _on_delete(e, it=item):
            await _delete(it["id"])

        async def _on_reject(e, it=item):
            await _reject(it["id"])

        actions: list[ft.Control] = []
        if sq_status == "0":
            actions = [
                ft.TextButton("修改", on_click=_on_edit),
                ft.TextButton("发起申请", on_click=_on_apply),
                ft.TextButton("删除", on_click=_on_delete, style=ft.ButtonStyle(color=ft.colors.RED)),
            ]
        elif sq_status == "1":
            actions = [
                ft.TextButton("同意", on_click=_on_apply, style=ft.ButtonStyle(color=ft.colors.GREEN)),
                ft.TextButton("驳回", on_click=_on_reject, style=ft.ButtonStyle(color=ft.colors.RED)),
            ]
        elif sq_status == "2":
            actions = [
                ft.TextButton("删除", on_click=_on_delete, style=ft.ButtonStyle(color=ft.colors.RED)),
            ]

        card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row([
                        ft.Container(
                            content=ft.Text(status_text, size=11, color=ft.colors.WHITE),
                            bgcolor=status_color,
                            border_radius=4,
                            padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        ),
                        ft.Text(type_name, size=13, weight=ft.FontWeight.W_500),
                        ft.Text(item.get("zyzbh", ""), size=12, color=ft.colors.GREY_600, expand=True, text_align=ft.TextAlign.RIGHT),
                    ]),
                    ft.Text(f"申请时间: {item.get('createTime', '')}", size=12, color=ft.colors.GREY_600),
                    ft.Row([
                        ft.Text(f"申请人: {item.get('sqr_dictText', '')}", size=12, color=ft.colors.GREY_600, expand=True),
                        ft.Text(f"审核人: {item.get('shry_dictText', '')}", size=12, color=ft.colors.GREY_600),
                    ]),
                    ft.Text(f"作业内容: {item.get('zynr', '')}", size=12, color=ft.colors.GREY_700),
                    ft.Row(controls=actions, spacing=4) if actions else ft.Container(),
                ],
                spacing=4,
            ),
            padding=ft.padding.all(12),
            bgcolor=ft.colors.WHITE,
            border_radius=8,
            margin=ft.margin.symmetric(horizontal=12, vertical=4),
        )
        return card

    async def _change_status(record_id: str):
        try:
            await svc.zysq_status(record_id)
            page.open(ft.SnackBar(ft.Text("操作成功")))
            await _load(reset=True)
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"操作失败：{ex}")))
            await page.update_async()

    async def _reject(record_id: str):
        try:
            await svc.zysq_status_no(record_id)
            page.open(ft.SnackBar(ft.Text("已驳回")))
            await _load(reset=True)
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"操作失败：{ex}")))
            await page.update_async()

    async def _delete(record_id: str):
        async def _confirm_delete(e):
            try:
                await svc.zysq_delete(record_id)
                dlg.open = False
                page.open(ft.SnackBar(ft.Text("删除成功")))
                await _load(reset=True)
            except Exception as ex:
                page.open(ft.SnackBar(ft.Text(f"删除失败：{ex}")))
                await page.update_async()

        async def _cancel(e):
            dlg.open = False
            await page.update_async()

        dlg = ft.AlertDialog(
            title=ft.Text("确认删除"),
            content=ft.Text("确定要删除这条申请记录吗？"),
            actions=[
                ft.TextButton("取消", on_click=_cancel),
                ft.ElevatedButton("删除", on_click=_confirm_delete, bgcolor=ft.colors.RED, color=ft.colors.WHITE),
            ],
        )
        page.dialog = dlg
        dlg.open = True
        await page.update_async()

    # --- 新增/编辑表单（全屏 View，避免 dialog 套 dialog） ---
    async def _show_form(existing: dict | None = None):
        form = {
            "id": existing.get("id", "") if existing else "",
            "zyzbh": existing.get("zyzbh", "") if existing else "",
            "zylx": existing.get("zylx", "") if existing else "",
            "sqdw": existing.get("sqdw", "") if existing else "",
            "sqr": existing.get("sqr", "") if existing else "",
            "shry": existing.get("shry", "") if existing else "",
            "zydd": existing.get("zydd", "") if existing else "",
            "zydw": existing.get("zydw", "") if existing else "",
            "zynr": existing.get("zynr", "") if existing else "",
            "zykssj": existing.get("zykssj", "") if existing else "",
            "zyjssj": existing.get("zyjssj", "") if existing else "",
        }

        display_refs: dict[str, ft.Text] = {}

        def _display_name(key: str, options: list[dict], multi: bool) -> str:
            val = str(form.get(key, ""))
            if not val:
                return "请选择"
            if multi:
                vals = [v for v in val.split(",") if v]
                names = [o["text"] for o in options if str(o["value"]) in vals]
                return ", ".join(names) if names else "请选择"
            for o in options:
                if str(o["value"]) == val:
                    return o["text"]
            return "请选择"

        def _refresh_display(key: str, options: list[dict], multi: bool):
            txt = display_refs.get(key)
            if txt is None:
                return
            name = _display_name(key, options, multi)
            txt.value = name
            txt.color = ft.colors.BLACK87 if name != "请选择" else ft.colors.GREY_600

        # ---- 单选弹窗 ----
        async def _show_single(key: str, options: list[dict], title: str):
            state = {"val": str(form.get(key, ""))}
            list_col = ft.Column(scroll=ft.ScrollMode.AUTO, tight=True, spacing=0)

            def _rebuild(query: str = ""):
                list_col.controls.clear()
                q = (query or "").strip()
                for o in options:
                    label = str(o.get("text", ""))
                    if q and q not in label:
                        continue
                    val = str(o.get("value", ""))
                    is_sel = val == state["val"]

                    def _make_click(v):
                        async def _on(e):
                            state["val"] = v
                            _rebuild(search_tf.value or "")
                            await page.update_async()
                        return _on

                    list_col.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(
                                    ft.icons.RADIO_BUTTON_CHECKED if is_sel else ft.icons.RADIO_BUTTON_UNCHECKED,
                                    size=18,
                                    color=ft.colors.BLUE if is_sel else ft.colors.GREY_400,
                                ),
                                ft.Text(label, size=14),
                            ]),
                            on_click=_make_click(val),
                            padding=ft.padding.symmetric(horizontal=10, vertical=8),
                            ink=True,
                        )
                    )
                if not list_col.controls:
                    list_col.controls.append(
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
                form[key] = state["val"]
                _refresh_display(key, options, multi=False)
                dlg.open = False
                await page.update_async()

            async def _cancel(e):
                dlg.open = False
                await page.update_async()

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text(title, size=16),
                content=ft.Container(
                    content=ft.Column([
                        search_tf,
                        ft.Container(
                            content=list_col,
                            height=360,
                            border=ft.border.all(1, ft.colors.GREY_200),
                            border_radius=4,
                        ),
                    ], tight=True, spacing=8),
                    width=320,
                ),
                actions=[
                    ft.TextButton("取消", on_click=_cancel),
                    ft.ElevatedButton("确定", on_click=_confirm),
                ],
            )
            page.dialog = dlg
            dlg.open = True
            await page.update_async()

        # ---- 多选弹窗 ----
        async def _show_multi(key: str, options: list[dict], title: str):
            selected: set[str] = set(v for v in str(form.get(key, "")).split(",") if v)
            list_col = ft.Column(scroll=ft.ScrollMode.AUTO, tight=True, spacing=0)

            def _make_on_cb(val: str):
                def _on(e):
                    if e.control.value:
                        selected.add(val)
                    else:
                        selected.discard(val)
                return _on

            def _rebuild(query: str = ""):
                list_col.controls.clear()
                q = (query or "").strip()
                for o in options:
                    label = str(o.get("text", ""))
                    if q and q not in label:
                        continue
                    val = str(o.get("value", ""))
                    list_col.controls.append(
                        ft.Checkbox(
                            label=label,
                            value=val in selected,
                            data=val,
                            on_change=_make_on_cb(val),
                        )
                    )
                if not list_col.controls:
                    list_col.controls.append(
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
                form[key] = ",".join(sorted(selected))
                _refresh_display(key, options, multi=True)
                dlg.open = False
                await page.update_async()

            async def _cancel(e):
                dlg.open = False
                await page.update_async()

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text(title, size=16),
                content=ft.Container(
                    content=ft.Column([
                        search_tf,
                        ft.Container(
                            content=list_col,
                            height=360,
                            border=ft.border.all(1, ft.colors.GREY_200),
                            border_radius=4,
                        ),
                    ], tight=True, spacing=8),
                    width=320,
                ),
                actions=[
                    ft.TextButton("取消", on_click=_cancel),
                    ft.ElevatedButton("确定", on_click=_confirm),
                ],
            )
            page.dialog = dlg
            dlg.open = True
            await page.update_async()

        # ---- 日期时间选择 ----
        async def _show_datetime(key: str):
            now = datetime.datetime.now()
            cur = str(form.get(key, ""))
            dt = now
            if cur:
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                    try:
                        dt = datetime.datetime.strptime(cur, fmt)
                        break
                    except ValueError:
                        continue

            def _dd(vals, value, width):
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
            days = [f"{d:02d}" for d in range(1, 32)]
            hours = [f"{h:02d}" for h in range(0, 24)]
            mins = [f"{m:02d}" for m in range(0, 60)]
            secs = [f"{s:02d}" for s in range(0, 60)]

            y_dd = _dd(years, str(dt.year), 90)
            mo_dd = _dd(months, f"{dt.month:02d}", 70)
            d_dd = _dd(days, f"{dt.day:02d}", 70)
            h_dd = _dd(hours, f"{dt.hour:02d}", 70)
            mi_dd = _dd(mins, f"{dt.minute:02d}", 70)
            s_dd = _dd(secs, f"{dt.second:02d}", 70)

            def _label(t):
                return ft.Text(t, size=13, color=ft.colors.GREY_700)

            async def _confirm(e):
                val = f"{y_dd.value}-{mo_dd.value}-{d_dd.value} {h_dd.value}:{mi_dd.value}:{s_dd.value}"
                form[key] = val
                txt = display_refs.get(key)
                if txt is not None:
                    txt.value = val
                    txt.color = ft.colors.BLACK87
                dlg.open = False
                await page.update_async()

            async def _cancel(e):
                dlg.open = False
                await page.update_async()

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("选择时间", size=16),
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([y_dd, _label("年"), mo_dd, _label("月"), d_dd, _label("日")], spacing=4),
                        ft.Row([h_dd, _label("时"), mi_dd, _label("分"), s_dd, _label("秒")], spacing=4),
                    ], tight=True, spacing=12),
                    width=360,
                ),
                actions=[
                    ft.TextButton("取消", on_click=_cancel),
                    ft.ElevatedButton("确定", on_click=_confirm),
                ],
            )
            page.dialog = dlg
            dlg.open = True
            await page.update_async()

        # ---- 字段控件 ----
        def _make_tf(key: str, hint: str, read_only: bool = False):
            def _on_change(e, k=key):
                form[k] = e.control.value
            return ft.TextField(
                value=form.get(key, ""),
                hint_text=hint,
                read_only=read_only,
                on_change=_on_change,
                border_color=ft.colors.GREY_300,
                focused_border_color=ft.colors.BLUE,
                content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
                text_size=14,
            )

        def _make_picker(key: str, options: list[dict], multi: bool, title: str, placeholder: str = "请选择"):
            name = _display_name(key, options, multi)
            txt = ft.Text(
                name,
                size=14,
                color=ft.colors.BLACK87 if name != placeholder else ft.colors.GREY_600,
                expand=True,
            )
            display_refs[key] = txt

            def _make_handler(k, opts, m, t):
                async def _on(e):
                    if m:
                        await _show_multi(k, opts, t)
                    else:
                        await _show_single(k, opts, t)
                return _on

            return ft.Container(
                content=ft.Row([
                    txt,
                    ft.Icon(ft.icons.ARROW_DROP_DOWN, size=20, color=ft.colors.GREY_400),
                ]),
                on_click=_make_handler(key, options, multi, title),
                padding=ft.padding.symmetric(horizontal=10, vertical=10),
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=4,
                ink=True,
            )

        def _make_dt(key: str):
            val = form.get(key, "")
            txt = ft.Text(
                val if val else "请选择时间",
                size=14,
                color=ft.colors.BLACK87 if val else ft.colors.GREY_600,
                expand=True,
            )
            display_refs[key] = txt

            def _make_handler(k):
                async def _on(e):
                    await _show_datetime(k)
                return _on

            return ft.Container(
                content=ft.Row([
                    txt,
                    ft.Icon(ft.icons.CALENDAR_TODAY, size=18, color=ft.colors.GREY_400),
                ]),
                on_click=_make_handler(key),
                padding=ft.padding.symmetric(horizontal=10, vertical=10),
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=4,
                ink=True,
            )

        def _row(label: str, control: ft.Control, required: bool = False):
            label_parts = []
            if required:
                label_parts.append(ft.Text("*", color=ft.colors.RED, size=14))
            label_parts.append(ft.Text(label, size=14, color=ft.colors.GREY_700, width=130))
            return ft.Container(
                content=ft.Row([
                    ft.Row(label_parts, spacing=2, tight=True),
                    ft.Container(content=control, expand=True),
                ], vertical_alignment=ft.CrossAxisAlignment.START),
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                bgcolor=ft.colors.WHITE,
            )

        # 作业类型（Dropdown）
        def _on_type_change(e):
            form["zylx"] = e.control.value
        type_dd = ft.Dropdown(
            value=form["zylx"] or None,
            hint_text="请选择作业类型",
            options=[ft.dropdown.Option(key=o["value"], text=o["text"]) for o in type_options],
            on_change=_on_type_change,
            border_color=ft.colors.GREY_300,
            text_size=14,
            dense=True,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
        )

        form_rows = ft.Column(
            controls=[
                _row("作业证编号", _make_tf("zyzbh", "自动生成,无需输入", read_only=True)),
                _row("作业类型", type_dd, required=True),
                _row("申请部门", _make_picker("sqdw", departs, False, "选择申请部门"), required=True),
                _row("申请人", _make_picker("sqr", peoples, False, "选择申请人"), required=True),
                _row("审核人", _make_picker("shry", peoples, True, "选择审核人"), required=True),
                _row("作业地点", _make_tf("zydd", "请输入作业地点"), required=True),
                _row("作业单位", _make_tf("zydw", "请输入作业单位"), required=True),
                _row("作业内容", _make_tf("zynr", "请输入作业内容"), required=True),
                _row("预计作业开始时间", _make_dt("zykssj"), required=True),
                _row("预计作业结束时间", _make_dt("zyjssj"), required=True),
            ],
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        async def _save(e):
            missing = []
            if not form["zylx"]: missing.append("作业类型")
            if not form["sqdw"]: missing.append("申请部门")
            if not form["sqr"]: missing.append("申请人")
            if not form["shry"]: missing.append("审核人")
            if not form["zydd"]: missing.append("作业地点")
            if not form["zydw"]: missing.append("作业单位")
            if not form["zynr"]: missing.append("作业内容")
            if not form["zykssj"]: missing.append("预计作业开始时间")
            if not form["zyjssj"]: missing.append("预计作业结束时间")

            if missing:
                page.open(ft.SnackBar(ft.Text(f"请填写：{', '.join(missing[:3])}{'...' if len(missing) > 3 else ''}")))
                await page.update_async()
                return

            try:
                payload = {k: v for k, v in form.items() if k != "id" or v}
                if form["id"]:
                    await svc.zysq_edit(payload)
                else:
                    await svc.zysq_add(payload)
                page.open(ft.SnackBar(ft.Text("操作成功!")))
                cleanup_overlays(page)
                page.views.pop()
                await page.update_async()
                await _load(reset=True)
            except Exception as ex:
                page.open(ft.SnackBar(ft.Text(f"保存失败：{ex}")))
                await page.update_async()

        async def _cancel(e):
            cleanup_overlays(page)
            page.views.pop()
            await page.update_async()

        buttons = ft.Container(
            content=ft.Row([
                ft.OutlinedButton("取消", on_click=_cancel, expand=True),
                ft.ElevatedButton("保存", on_click=_save, bgcolor=ft.colors.BLUE, color=ft.colors.WHITE, expand=True),
            ], spacing=12),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
        )

        form_view = ft.View(
            route="/ticket/apply/form",
            appbar=ft.AppBar(
                title=ft.Text("编辑申请" if existing else "新增申请"),
                bgcolor=ft.colors.BLUE,
                color=ft.colors.WHITE,
            ),
            controls=[form_rows, buttons],
            padding=0,
            bgcolor=ft.colors.GREY_100,
        )
        page.views.append(form_view)
        await page.update_async()

    async def _on_add(e):
        await _show_form()

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

    view = ft.View(
        route="/ticket/apply",
        appbar=ft.AppBar(
            title=ft.Text("作业申请"),
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE,
            actions=[
                ft.IconButton(ft.icons.ADD, icon_color=ft.colors.WHITE, on_click=_on_add),
            ],
        ),
        controls=[scroll_content],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    await _init_sources()
    await _load(reset=True)

    return view
