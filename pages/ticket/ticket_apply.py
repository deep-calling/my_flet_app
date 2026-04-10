"""作业申请列表页 — 对应原 jobTicketSq/zysq.vue"""

from __future__ import annotations

from typing import Any

import flet as ft

from services import ticket_service as svc
from utils.app_state import app_state


# 作业类型码 → 名称映射（与 config.py 一致）
_TYPE_NAMES = {
    "3": "动火作业", "4": "受限空间作业", "5": "高处作业",
    "7": "吊装作业", "8": "临时用电作业", "10": "盲板抽堵作业",
    "11": "断路作业", "12": "动土作业",
}

# 申请状态
_STATUS_MAP = {
    "0": ("待审核", ft.colors.ORANGE),
    "1": ("审核中", ft.colors.BLUE),
    "2": ("已审核", ft.colors.GREEN),
}


async def build_ticket_apply_page(page: ft.Page) -> ft.View:
    """构建作业申请列表页"""

    # --- 状态 ---
    page_no = [1]
    page_size = 10
    items_data: list[dict] = []
    is_loading = [False]

    # 数据源
    type_options: list[dict] = []
    departs: list[dict] = []
    peoples: list[dict] = []

    # --- 控件 ---
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

    # --- 扁平化部门树 ---
    def _flatten_departs(tree: dict, result: list):
        if str(tree.get("delFlag", "0")) == "0":
            children = tree.get("children") or []
            if children:
                for child in children:
                    _flatten_departs(child, result)
            else:
                result.append({"id": tree["id"], "text": tree.get("departName", ""), "value": tree["id"]})

    # --- 初始化数据源 ---
    async def _init_sources():
        nonlocal type_options, departs, peoples
        try:
            type_result = await svc.get_dict_work_type()
            if isinstance(type_result, list):
                type_options = [{"text": r.get("text", ""), "value": r.get("value", "")} for r in type_result]
        except Exception:
            pass

        try:
            depart_result = await svc.get_depart_list()
            flat: list[dict] = []
            if isinstance(depart_result, list) and depart_result:
                _flatten_departs(depart_result[0], flat)
            departs = flat
        except Exception:
            pass

        try:
            people_result = await svc.get_people_list()
            records = people_result.get("records", []) if isinstance(people_result, dict) else []
            peoples = [{"id": r["id"], "text": r.get("xm", ""), "value": r["id"]} for r in records]
        except Exception:
            pass

    # --- 加载列表 ---
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
            page.snack_bar = ft.SnackBar(ft.Text(f"加载失败：{ex}"), open=True)

        is_loading[0] = False
        loading_ring.visible = False
        await page.update_async()

    async def _on_load_more(e):
        page_no[0] += 1
        await _load(reset=False)

    # --- 构建列表项 ---
    def _build_item(item: dict) -> ft.Control:
        sq_status = str(item.get("sqStatus", "0"))
        status_text, status_color = _STATUS_MAP.get(sq_status, ("未知", ft.colors.GREY))
        type_name = _TYPE_NAMES.get(str(item.get("zylx", "")), "")

        # 操作按钮
        actions: list[ft.Control] = []
        if sq_status == "0":
            actions = [
                ft.TextButton("修改", on_click=lambda e, it=item: _show_form(it)),
                ft.TextButton("发起申请", on_click=lambda e, it=item: _change_status(it["id"])),
                ft.TextButton("删除", on_click=lambda e, it=item: _delete(it["id"]), style=ft.ButtonStyle(color=ft.colors.RED)),
            ]
        elif sq_status == "1":
            actions = [
                ft.TextButton("同意", on_click=lambda e, it=item: _change_status(it["id"]), style=ft.ButtonStyle(color=ft.colors.GREEN)),
                ft.TextButton("驳回", on_click=lambda e, it=item: _reject(it["id"]), style=ft.ButtonStyle(color=ft.colors.RED)),
            ]
        elif sq_status == "2":
            actions = [
                ft.TextButton("删除", on_click=lambda e, it=item: _delete(it["id"]), style=ft.ButtonStyle(color=ft.colors.RED)),
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

    # --- 操作 ---
    async def _change_status(record_id: str):
        try:
            await svc.zysq_status(record_id)
            page.snack_bar = ft.SnackBar(ft.Text("操作成功"), open=True)
            await _load(reset=True)
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"操作失败：{ex}"), open=True)
            await page.update_async()

    async def _reject(record_id: str):
        try:
            await svc.zysq_status_no(record_id)
            page.snack_bar = ft.SnackBar(ft.Text("已驳回"), open=True)
            await _load(reset=True)
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"操作失败：{ex}"), open=True)
            await page.update_async()

    async def _delete(record_id: str):
        async def _confirm_delete(e):
            try:
                await svc.zysq_delete(record_id)
                dlg.open = False
                page.snack_bar = ft.SnackBar(ft.Text("删除成功"), open=True)
                await _load(reset=True)
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"删除失败：{ex}"), open=True)
                await page.update_async()

        dlg = ft.AlertDialog(
            title=ft.Text("确认删除"),
            content=ft.Text("确定要删除这条申请记录吗？"),
            actions=[
                ft.TextButton("取消", on_click=lambda e: _close_dlg(dlg)),
                ft.ElevatedButton("删除", on_click=_confirm_delete, bgcolor=ft.colors.RED, color=ft.colors.WHITE),
            ],
        )
        page.dialog = dlg
        dlg.open = True
        await page.update_async()

    def _close_dlg(dlg):
        dlg.open = False
        page.update()

    # --- 新增/编辑表单弹窗 ---
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

        # 类型选择
        type_dd = ft.Dropdown(
            value=form["zylx"] or None,
            hint_text="请选择作业类型",
            options=[ft.dropdown.Option(key=o["value"], text=o["text"]) for o in type_options],
            on_change=lambda e: form.__setitem__("zylx", e.control.value),
            border_color=ft.colors.GREY_300,
            text_size=14,
        )

        def _make_tf(key: str, hint: str):
            return ft.TextField(
                value=form.get(key, ""),
                hint_text=hint,
                on_change=lambda e, k=key: form.__setitem__(k, e.control.value),
                border_color=ft.colors.GREY_300,
                text_size=14,
            )

        # 人员/部门选择按钮
        async def _select_single(key: str, options: list[dict], title: str):
            async def _pick(val, dlg2):
                form[key] = val
                dlg2.open = False
                await page.update_async()

            tiles = [
                ft.ListTile(
                    title=ft.Text(o["text"]),
                    on_click=lambda e, v=o["value"]: _pick(v, pick_dlg),
                ) for o in options
            ]
            pick_dlg = ft.AlertDialog(
                title=ft.Text(title),
                content=ft.Container(
                    content=ft.Column(tiles, scroll=ft.ScrollMode.AUTO, tight=True),
                    height=400, width=300,
                ),
            )
            page.dialog = pick_dlg
            pick_dlg.open = True
            await page.update_async()

        async def _select_multi(key: str, options: list[dict], title: str):
            selected = set(form.get(key, "").split(",")) if form.get(key) else set()
            cbs = [ft.Checkbox(label=o["text"], value=str(o["value"]) in selected, data=str(o["value"])) for o in options]

            async def _ok(e):
                form[key] = ",".join(cb.data for cb in cbs if cb.value)
                pick_dlg.open = False
                await page.update_async()

            pick_dlg = ft.AlertDialog(
                title=ft.Text(title),
                content=ft.Container(
                    content=ft.Column(cbs, scroll=ft.ScrollMode.AUTO, tight=True),
                    height=400, width=300,
                ),
                actions=[ft.ElevatedButton("确定", on_click=_ok)],
            )
            page.dialog = pick_dlg
            pick_dlg.open = True
            await page.update_async()

        form_controls = [
            ft.Text("作业证编号", size=12, color=ft.colors.GREY_600),
            ft.TextField(value=form["zyzbh"], read_only=True, border_color=ft.colors.GREY_300, text_size=14),
            ft.Text("作业类型 *", size=12, color=ft.colors.GREY_600),
            type_dd,
            ft.Text("申请部门 *", size=12, color=ft.colors.GREY_600),
            ft.Container(
                content=ft.Text(form.get("sqdw", "") or "请选择", size=14),
                on_click=lambda e: _select_single("sqdw", departs, "选择部门"),
                padding=10, border=ft.border.all(1, ft.colors.GREY_300), border_radius=4,
            ),
            ft.Text("申请人 *", size=12, color=ft.colors.GREY_600),
            ft.Container(
                content=ft.Text(form.get("sqr", "") or "请选择", size=14),
                on_click=lambda e: _select_single("sqr", peoples, "选择申请人"),
                padding=10, border=ft.border.all(1, ft.colors.GREY_300), border_radius=4,
            ),
            ft.Text("审核人 *", size=12, color=ft.colors.GREY_600),
            ft.Container(
                content=ft.Text(form.get("shry", "") or "请选择", size=14),
                on_click=lambda e: _select_multi("shry", peoples, "选择审核人"),
                padding=10, border=ft.border.all(1, ft.colors.GREY_300), border_radius=4,
            ),
            ft.Text("作业地点 *", size=12, color=ft.colors.GREY_600),
            _make_tf("zydd", "请输入作业地点"),
            ft.Text("作业单位 *", size=12, color=ft.colors.GREY_600),
            _make_tf("zydw", "请输入作业单位"),
            ft.Text("作业内容 *", size=12, color=ft.colors.GREY_600),
            _make_tf("zynr", "请输入作业内容"),
        ]

        async def _save(e):
            # 校验必填
            if not form["zylx"] or not form["sqdw"] or not form["sqr"] or not form["shry"]:
                page.snack_bar = ft.SnackBar(ft.Text("请填写必填项"), open=True)
                await page.update_async()
                return

            try:
                if form["id"]:
                    await svc.zysq_edit(form)
                else:
                    await svc.zysq_add(form)

                dlg.open = False
                page.snack_bar = ft.SnackBar(ft.Text("保存成功"), open=True)
                await _load(reset=True)
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"保存失败：{ex}"), open=True)
                await page.update_async()

        dlg = ft.AlertDialog(
            title=ft.Text("编辑申请" if existing else "新增申请", size=16),
            content=ft.Container(
                content=ft.Column(form_controls, scroll=ft.ScrollMode.AUTO, spacing=6),
                height=500, width=350,
            ),
            actions=[
                ft.TextButton("取消", on_click=lambda e: _close_dlg(dlg)),
                ft.ElevatedButton("保存", on_click=_save, bgcolor=ft.colors.BLUE, color=ft.colors.WHITE),
            ],
        )
        page.dialog = dlg
        dlg.open = True
        await page.update_async()

    # --- 新增按钮 ---
    async def _on_add(e):
        await _show_form()

    # --- 组装页面 ---
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

    # 首次加载
    await _init_sources()
    await _load(reset=True)

    return view
