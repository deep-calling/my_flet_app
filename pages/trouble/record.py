"""排查记录列表 + 编辑弹窗 — trouble / bbzrz 共用"""

from __future__ import annotations

from datetime import datetime

import flet as ft

from services import trouble_service as ts
from components.status_badge import status_badge


async def build_record_view(page: ft.Page, module_type: str = "trouble") -> ft.View:
    """排查记录列表页，点击可弹窗编辑。"""
    is_bbzrz = module_type == "bbzrz"
    title = "包保排查记录" if is_bbzrz else "隐患排查记录"

    # --- 状态 ---
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
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        alignment=ft.alignment.center,
        padding=ft.padding.only(top=120),
        visible=False,
    )

    # 字典：检查结果选项
    check_status_options: list[dict] = []

    async def _load_dict():
        try:
            items = await ts.get_danger_dict("check_result")
            if isinstance(items, list):
                check_status_options.clear()
                for it in items:
                    check_status_options.append({
                        "text": it.get("text", it.get("title", "")),
                        "value": str(it.get("value", "")),
                    })
        except Exception:
            pass

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
            result = await ts.get_check_record_list(
                {"pageNo": current_page[0], "pageSize": page_size},
                module_type=module_type,
            )
            records = result.get("records", []) if isinstance(result, dict) else []
            total = result.get("total", 0) if isinstance(result, dict) else 0

            for item in records:
                items_data.append(item)
                ctrl = _build_item(item)

                def _make_click(data):
                    async def _click(e):
                        await _show_edit_dialog(data)
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

    def _build_item(item: dict) -> ft.Control:
        """构建列表项，与原项目保持一致：任务名称、排查时间、排查结果、记录描述"""

        def _row(label: str, value: str) -> ft.Row:
            return ft.Row(
                controls=[
                    ft.Text(label, size=14, color=ft.colors.GREY_800, no_wrap=True),
                    ft.Text(
                        value or "-", size=14, color=ft.colors.GREY_600,
                        expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                spacing=4,
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    _row("隐患排查任务名称:", item.get("checkTaskId_dictText", item.get("taskName", ""))),
                    _row("排查时间:", item.get("checkTime", "")),
                    _row("排查结果:", item.get("checkStatus_dictText", item.get("checkStatusName", ""))),
                    _row("隐患排查记录描述:", item.get("checkRecordDesc", "")),
                ],
                spacing=6,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
            border_radius=8,
            margin=ft.margin.only(top=10, left=16, right=16),
        )

    # --- 编辑弹窗 ---
    async def _show_edit_dialog(item: dict):
        # 保留完整的 item 数据用于提交
        form_data = dict(item)

        desc_field = ft.TextField(
            value=item.get("checkRecordDesc", ""),
            hint_text="请输入",
            multiline=True, min_lines=3, max_lines=5,
            border_color=ft.colors.GREY_300,
            text_size=14,
        )

        status_dd = ft.Dropdown(
            value=item.get("checkStatus", "") or None,
            hint_text="请选择",
            options=[ft.dropdown.Option(key=o["value"], text=o["text"]) for o in check_status_options],
            border_color=ft.colors.GREY_300,
            text_size=14,
        )

        def _label_row(label: str, value: str) -> ft.Row:
            return ft.Row(
                controls=[
                    ft.Text(label, size=13, color=ft.colors.GREY_700, no_wrap=True),
                    ft.Text(value or "-", size=13, color=ft.colors.GREY_800, expand=True),
                ],
                spacing=4,
            )

        async def _save(ev):
            # 提交时更新排查时间为当前时间（与原项目一致）
            form_data["checkTime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            form_data["checkRecordDesc"] = desc_field.value or ""
            form_data["checkStatus"] = status_dd.value or ""
            # 更新 checkStatusName 用于回显
            for o in check_status_options:
                if o["value"] == form_data["checkStatus"]:
                    form_data["checkStatusName"] = o["text"]
                    break
            try:
                await ts.update_check_record(form_data)
                page.snack_bar = ft.SnackBar(ft.Text("添加成功"), open=True)
                dlg.open = False
                await page.update_async()
                await _load_data(reset=True)
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"保存失败：{ex}"), open=True)
                await page.update_async()

        async def _cancel(ev):
            dlg.open = False
            await page.update_async()

        dlg = ft.AlertDialog(
            title=ft.Text("检查"),
            content=ft.Column(
                controls=[
                    # 只读字段：任务名称、排查时间
                    _label_row("隐患排查任务名称",
                               item.get("checkTaskId_dictText", item.get("taskName", ""))),
                    ft.Container(height=4),
                    _label_row("排查时间", item.get("checkTime", "")),
                    ft.Container(height=8),
                    ft.Text("排查结果", size=13, color=ft.colors.GREY_700),
                    status_dd,
                    ft.Container(height=8),
                    ft.Text("隐患排查记录描述", size=13, color=ft.colors.GREY_700),
                    desc_field,
                ],
                tight=True,
                spacing=4,
                width=320,
            ),
            actions=[
                ft.TextButton("取消", on_click=_cancel),
                ft.ElevatedButton("提交", on_click=_save),
            ],
        )
        page.dialog = dlg
        dlg.open = True
        await page.update_async()

    # --- 组装 ---
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
        route=f"/{module_type}/record",
        appbar=ft.AppBar(title=ft.Text(title), bgcolor=ft.colors.WHITE),
        controls=[scroll_content],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    # 先加载字典再加载数据
    await _load_dict()
    await _load_data(reset=True)
    return view
