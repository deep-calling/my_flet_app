"""隐患任务列表 + 详情 + 检查结论 + 隐患上报 + 检查条目列表
trouble / bbzrz 共用，通过 module_type 参数区分"""

from __future__ import annotations

import flet as ft
from datetime import datetime

from services import trouble_service as ts
from components.list_page import build_list_page
from components.detail_page import build_detail_page, detail_section
from components.form_fields import (
    readonly_field, textarea_field, dropdown_field, date_field, form_item,
)
from components.image_upload import ImageUpload
from components.status_badge import status_badge


# Tab 配置：(标签名, 状态值)
_TABS = [
    ("待检查", "1"),
    ("超期未检查", "4"),
    ("已检查", "2"),
]

# 状态码 → 显示文本
_STATUS_MAP = {"1": "待检查", "2": "已检查", "4": "超期未检查"}


# ============================================================
# 任务列表页
# ============================================================

async def build_tasks_view(page: ft.Page, module_type: str = "trouble") -> ft.View:
    """构建隐患任务列表页。

    module_type: 'trouble' (隐患排查) 或 'bbzrz' (包保责任制)
    """
    is_bbzrz = module_type == "bbzrz"
    title = "包保责任制任务" if is_bbzrz else "隐患任务"
    task_type = "1" if is_bbzrz else "0"

    # 当前选中的 Tab 索引
    current_tab = [0]

    # --- 控件引用 ---
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

    # 分页状态
    current_page = [1]
    page_size = 10
    items_data: list[dict] = []
    is_loading = [False]

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
            status = _TABS[current_tab[0]][1]
            result = await ts.get_task_list({
                "taskType": task_type,
                "status": status,
                "pageNo": current_page[0],
                "pageSize": page_size,
            })
            records = result.get("records", []) if isinstance(result, dict) else []
            total = result.get("total", 0) if isinstance(result, dict) else 0

            for item in records:
                items_data.append(item)
                ctrl = _build_task_item(item)

                def _make_click(data):
                    async def _click(e):
                        await page.go_async(f"/{module_type}/tasks/detail?id={data['id']}")
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

    def _build_task_item(item: dict) -> ft.Control:
        """渲染单个任务卡片"""
        jczt = str(item.get("jczt", ""))
        status_text = _STATUS_MAP.get(jczt, jczt)

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                item.get("rwmc", ""),
                                size=15, weight=ft.FontWeight.W_500,
                                expand=True, max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            status_badge(status_text),
                        ],
                    ),
                    ft.Text(
                        f"任务编号：{item.get('rwbh', '-')}",
                        size=13, color=ft.colors.GREY_600,
                    ),
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"检查人：{item.get('jcr_dictText', '-')}",
                                size=12, color=ft.colors.GREY_500, expand=True,
                            ),
                            ft.Text(
                                item.get("jclx_dictText", ""),
                                size=12, color=ft.colors.GREY_500,
                            ),
                        ],
                    ),
                ],
                spacing=4,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200)),
        )

    # --- Tab 栏 ---
    async def _on_tab_change(e):
        current_tab[0] = e.control.selected_index
        await _load_data(reset=True)

    tabs = ft.Tabs(
        selected_index=0,
        on_change=_on_tab_change,
        tabs=[ft.Tab(text=label) for label, _ in _TABS],
        label_color=ft.colors.BLUE,
        unselected_label_color=ft.colors.GREY_600,
        indicator_color=ft.colors.BLUE,
        divider_color=ft.colors.GREY_200,
    )

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

    body = ft.Column(controls=[tabs, scroll_content], spacing=0, expand=True)

    view = ft.View(
        route=f"/{module_type}/tasks",
        appbar=ft.AppBar(title=ft.Text(title), bgcolor=ft.colors.WHITE),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    await _load_data(reset=True)
    return view


# ============================================================
# 任务详情页
# ============================================================

async def build_task_detail_view(
    page: ft.Page, record_id: str, module_type: str = "trouble"
) -> ft.View:
    """隐患任务详情页"""
    is_bbzrz = module_type == "bbzrz"
    title = "包保任务详情" if is_bbzrz else "隐患任务详情"

    async def _load(rid: str) -> dict:
        detail = await ts.get_task_detail(rid)
        # 同时获取统计
        try:
            counts = await ts.get_record_count(rid)
            if isinstance(counts, dict):
                detail.update(counts)
        except Exception:
            pass
        return detail

    def _build_content(data: dict) -> ft.Control:
        jczt = str(data.get("jczt", ""))

        # 基本信息
        basic = detail_section("基本信息", [
            readonly_field("任务编号", data.get("rwbh", "")),
            readonly_field("任务名称", data.get("rwmc", "")),
            readonly_field("检查类型", data.get("jclx_dictText", "")),
            readonly_field("检查周期", f"{data.get('checkCycle', '')} {data.get('checkCycleUnit_dictText', '')}"),
            readonly_field("检查人", data.get("jcr_dictText", "")),
            readonly_field("所属部门", data.get("sjbm_dictText", "")),
            readonly_field("创建时间", data.get("createTime", "")),
        ])

        # 风险信息
        risk = detail_section("风险信息", [
            readonly_field("风险对象", data.get("riskAnalysisObjectId_dictText", "")),
            readonly_field("风险单元", data.get("riskAnalysisUnitId_dictText", "")),
            readonly_field("风险事件", data.get("riskAnalysisEventId_dictText", "")),
            readonly_field("管控措施", data.get("riskManageMeasureId_dictText", "")),
        ])

        # 统计信息
        stats = detail_section("检查统计", [
            readonly_field("全部", str(data.get("allCount", 0))),
            readonly_field("已完成", str(data.get("finishCount", 0))),
            readonly_field("待办", str(data.get("toDoCount", 0))),
            readonly_field("超期", str(data.get("overdueCount", 0))),
        ])

        return ft.Column(controls=[basic, risk, stats], spacing=0)

    # 动态操作按钮
    actions: list[dict] = []

    async def _on_check_finish(e):
        """跳转检查结论页"""
        await page.go_async(f"/{module_type}/tasks/check_finish?id={record_id}")

    async def _on_report(e):
        """跳转隐患上报页"""
        await page.go_async(f"/{module_type}/tasks/report?id={record_id}")

    async def _on_task_list(e):
        """跳转检查条目列表"""
        await page.go_async(f"/{module_type}/tasks/list?recordId={record_id}")

    # 获取详情判断状态后再决定按钮（在 build 之前先拉数据）
    try:
        pre_data = await ts.get_task_detail(record_id)
        jczt = str(pre_data.get("jczt", ""))
        if jczt in ("1", "4"):
            actions = [
                {"label": "开始检查", "on_click": _on_task_list, "style": "primary"},
                {"label": "检查结论", "on_click": _on_check_finish, "style": "primary"},
                {"label": "隐患上报", "on_click": _on_report, "style": "danger"},
            ]
    except Exception:
        pass

    return await build_detail_page(
        page,
        title=title,
        record_id=record_id,
        on_load_data=_load,
        build_content=_build_content,
        actions=actions,
    )


# ============================================================
# 检查结论页 (checkFinish)
# ============================================================

async def build_check_finish_view(
    page: ft.Page, record_id: str, module_type: str = "trouble"
) -> ft.View:
    """检查结论表单：排查记录描述 + 检查结论(字典) + 现场照片"""
    is_bbzrz = module_type == "bbzrz"
    title = "检查结论"

    # 表单控件
    desc_field = ft.TextField(
        hint_text="请输入隐患排查记录描述",
        multiline=True, min_lines=3, max_lines=5,
        border_color=ft.colors.GREY_300,
        focused_border_color=ft.colors.BLUE,
        text_size=14,
    )

    jcjl_dropdown = ft.Dropdown(
        hint_text="请选择检查结论",
        border_color=ft.colors.GREY_300,
        focused_border_color=ft.colors.BLUE,
        text_size=14,
        options=[],
    )

    image_upload = ImageUpload(page, max_count=9)

    # 加载字典
    try:
        dict_items = await ts.get_danger_dict("check_result")
        options = dict_items if isinstance(dict_items, list) else []
        jcjl_dropdown.options = [
            ft.dropdown.Option(
                key=item.get("value", item.get("id", "")),
                text=item.get("text", item.get("xm", "")),
            )
            for item in options
        ]
    except Exception:
        pass

    async def _submit(e):
        if not desc_field.value or not desc_field.value.strip():
            page.snack_bar = ft.SnackBar(ft.Text("请输入隐患排查记录描述"), open=True)
            await page.update_async()
            return
        if not jcjl_dropdown.value:
            page.snack_bar = ft.SnackBar(ft.Text("请选择检查结论"), open=True)
            await page.update_async()
            return

        data = {
            "id": record_id,
            "jcjl": jcjl_dropdown.value,
            "yhpcjlms": desc_field.value.strip(),
        }
        paths = image_upload.uploaded_paths
        if paths:
            data["xczp"] = ",".join(paths)

        try:
            await ts.check_finish(data)
            page.snack_bar = ft.SnackBar(ft.Text("提交成功"), open=True)
            await page.update_async()
            page.views.pop()
            await page.update_async()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"提交失败：{ex}"), open=True)
            await page.update_async()

    body = ft.ListView(
        controls=[
            # 隐患排查记录描述
            ft.Container(
                content=ft.Text("隐患排查记录描述", size=14, color=ft.colors.GREY_700),
                padding=ft.padding.only(left=16, top=16, bottom=8),
            ),
            ft.Container(
                content=desc_field,
                padding=ft.padding.symmetric(horizontal=16),
                bgcolor=ft.colors.WHITE,
            ),
            # 检查结论
            ft.Container(
                content=ft.Text("检查结论", size=14, color=ft.colors.GREY_700),
                padding=ft.padding.only(left=16, top=16, bottom=8),
            ),
            ft.Container(
                content=jcjl_dropdown,
                padding=ft.padding.symmetric(horizontal=16),
                bgcolor=ft.colors.WHITE,
            ),
            # 现场照片
            ft.Container(
                content=ft.Text("现场照片", size=14, color=ft.colors.GREY_700),
                padding=ft.padding.only(left=16, top=16, bottom=8),
            ),
            ft.Container(
                content=image_upload,
                padding=ft.padding.symmetric(horizontal=16),
                bgcolor=ft.colors.WHITE,
            ),
            # 提交按钮
            ft.Container(
                content=ft.ElevatedButton(
                    "提交", on_click=_submit,
                    bgcolor=ft.colors.BLUE, color=ft.colors.WHITE,
                    width=200,
                ),
                alignment=ft.alignment.center,
                padding=ft.padding.only(top=40, bottom=20),
            ),
        ],
        expand=True,
        padding=0,
    )

    return ft.View(
        route=f"/{module_type}/tasks/check_finish",
        appbar=ft.AppBar(title=ft.Text(title), bgcolor=ft.colors.WHITE),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )


# ============================================================
# 隐患上报页 (report) — 任务检查中上报
# ============================================================

async def build_report_view(
    page: ft.Page, record_id: str, module_type: str = "trouble"
) -> ft.View:
    """任务检查中的隐患上报表单：发现时间 + 隐患备注 + 现场照片"""
    title = "隐患上报"

    # 默认当前时间
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    time_field = ft.TextField(
        value=now_str,
        hint_text="请选择时间",
        border_color=ft.colors.GREY_300,
        focused_border_color=ft.colors.BLUE,
        text_size=14,
        suffix_icon=ft.icons.CALENDAR_TODAY,
    )

    remark_field = ft.TextField(
        hint_text="请输入隐患备注",
        multiline=True, min_lines=3, max_lines=5,
        border_color=ft.colors.GREY_300,
        focused_border_color=ft.colors.BLUE,
        text_size=14,
    )

    image_upload = ImageUpload(page, max_count=9)

    async def _submit(e):
        data = {
            "sfyyc": 0,
            "fxsj": time_field.value or now_str,
            "yhbz": remark_field.value or "",
            "recordId": record_id,
            "taskType": 0,
        }
        paths = image_upload.uploaded_paths
        if paths:
            data["xczp"] = ",".join(paths)

        try:
            await ts.check_report(data)
            page.snack_bar = ft.SnackBar(ft.Text("提交成功"), open=True)
            await page.update_async()
            page.views.pop()
            await page.update_async()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"提交失败：{ex}"), open=True)
            await page.update_async()

    body = ft.ListView(
        controls=[
            # 发现时间
            ft.Container(
                content=ft.Text("发现时间", size=14, color=ft.colors.GREY_700),
                padding=ft.padding.only(left=16, top=16, bottom=8),
            ),
            ft.Container(
                content=time_field,
                padding=ft.padding.symmetric(horizontal=16),
                bgcolor=ft.colors.WHITE,
            ),
            # 隐患备注
            ft.Container(
                content=ft.Text("隐患备注", size=14, color=ft.colors.GREY_700),
                padding=ft.padding.only(left=16, top=16, bottom=8),
            ),
            ft.Container(
                content=remark_field,
                padding=ft.padding.symmetric(horizontal=16),
                bgcolor=ft.colors.WHITE,
            ),
            # 现场照片
            ft.Container(
                content=ft.Text("现场照片", size=14, color=ft.colors.GREY_700),
                padding=ft.padding.only(left=16, top=16, bottom=8),
            ),
            ft.Container(
                content=image_upload,
                padding=ft.padding.symmetric(horizontal=16),
                bgcolor=ft.colors.WHITE,
            ),
            # 提交按钮
            ft.Container(
                content=ft.ElevatedButton(
                    "提交", on_click=_submit,
                    bgcolor=ft.colors.BLUE, color=ft.colors.WHITE,
                    width=200,
                ),
                alignment=ft.alignment.center,
                padding=ft.padding.only(top=40, bottom=20),
            ),
        ],
        expand=True,
        padding=0,
    )

    return ft.View(
        route=f"/{module_type}/tasks/report",
        appbar=ft.AppBar(title=ft.Text(title), bgcolor=ft.colors.WHITE),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )


# ============================================================
# 检查条目列表页 (task item list)
# ============================================================

async def build_task_item_list_view(
    page: ft.Page, record_id: str, module_type: str = "trouble"
) -> ft.View:
    """检查条目列表：检查项分类选择 + 条目列表 + 正常/异常弹窗"""
    title = "任务列表"

    # 状态
    items: list[dict] = []  # 检查项列表
    selected_item = [{}]  # 当前选中的检查项
    entries: list[dict] = []  # 条目列表
    current_page_no = [1]
    page_size = 10
    is_loading = [False]

    # 控件
    item_btn_text = ft.Text("请选择检查项", size=14, color=ft.colors.GREY_700)
    entries_column = ft.Column(spacing=0, expand=True)
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

    # --- 加载检查项列表 ---
    try:
        item_result = await ts.get_item_list({"recordId": record_id})
        items = item_result if isinstance(item_result, list) else []
        if items:
            selected_item[0] = items[0]
            item_btn_text.value = items[0].get("jcxm", "请选择检查项")
    except Exception:
        pass

    # --- 加载条目 ---
    async def _load_entries(reset: bool = False):
        if is_loading[0]:
            return
        if not selected_item[0]:
            return
        is_loading[0] = True
        loading_ring.visible = True
        await page.update_async()

        if reset:
            current_page_no[0] = 1
            entries.clear()
            entries_column.controls.clear()

        try:
            result = await ts.get_entry_list({
                "recordId": record_id,
                "itemId": selected_item[0].get("id", ""),
                "pageNo": current_page_no[0],
                "pageSize": page_size,
                "taskType": 0,
            })
            records = result.get("records", []) if isinstance(result, dict) else []
            total = result.get("total", 0) if isinstance(result, dict) else 0

            for entry in records:
                entries.append(entry)
                entries_column.controls.append(_build_entry(entry))

            has_more = len(entries) < total
            load_more_btn.visible = has_more
            if has_more:
                load_more_btn.content = ft.TextButton(
                    "加载更多", on_click=_on_load_more,
                    style=ft.ButtonStyle(color=ft.colors.BLUE),
                )
            empty_widget.visible = len(entries) == 0
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"加载失败：{ex}"), open=True)

        is_loading[0] = False
        loading_ring.visible = False
        await page.update_async()

    async def _on_load_more(e):
        current_page_no[0] += 1
        await _load_entries(reset=False)

    def _build_entry(entry: dict) -> ft.Control:
        """渲染单个检查条目"""
        jczt = entry.get("jczt")
        checked = jczt is not None and str(jczt) != "1"

        def _make_click(data):
            async def _click(e):
                if str(data.get("jczt", "")) == "2":
                    return  # 已检查不可操作
                await _show_check_modal(data)
            return _click

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        entry.get("jcnr", ""),
                        size=14, expand=True,
                        color=ft.colors.BLACK87,
                    ),
                    ft.Icon(
                        ft.icons.CHECK_CIRCLE,
                        color=ft.colors.GREEN if checked else ft.colors.GREY_300,
                        size=24,
                    ) if checked else ft.Container(),
                ],
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            bgcolor=ft.colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200)),
            on_click=_make_click(entry),
            ink=True,
        )

    # --- 正常/异常弹窗 ---
    async def _show_check_modal(entry: dict):
        async def _on_normal(ev):
            await _submit_check(entry, sfyc=0)
            dlg.open = False
            await page.update_async()

        async def _on_abnormal(ev):
            await _submit_check(entry, sfyc=1)
            dlg.open = False
            await page.update_async()

        dlg = ft.AlertDialog(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text(entry.get("jcnr", ""), size=14),
                        padding=ft.padding.only(bottom=10),
                        border=ft.border.only(
                            bottom=ft.border.BorderSide(1, ft.colors.GREY_200)
                        ),
                    ),
                    ft.Text(entry.get("jcyj", ""), size=13, color=ft.colors.GREY_600),
                ],
                tight=True, spacing=10, width=280,
            ),
            actions=[
                ft.TextButton(
                    "异常", on_click=_on_abnormal,
                    style=ft.ButtonStyle(color=ft.colors.RED),
                ),
                ft.TextButton(
                    "正常", on_click=_on_normal,
                    style=ft.ButtonStyle(color=ft.colors.GREEN),
                ),
            ],
        )
        page.dialog = dlg
        dlg.open = True
        await page.update_async()

    async def _submit_check(entry: dict, sfyc: int):
        try:
            await ts.submit_content({
                "sfyc": sfyc,
                "contentId": entry.get("id", ""),
            })
            page.snack_bar = ft.SnackBar(ft.Text("操作成功"), open=True)
            await page.update_async()
            # 刷新列表
            await _load_entries(reset=True)
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"操作失败：{ex}"), open=True)
            await page.update_async()

    # --- 检查项选择器弹窗 ---
    async def _show_item_picker(e):
        if not items:
            return

        async def _pick(item):
            async def _handler(ev):
                selected_item[0] = item
                item_btn_text.value = item.get("jcxm", "")
                picker_dlg.open = False
                await page.update_async()
                await _load_entries(reset=True)
            return _handler

        sheet_items: list[ft.Control] = []
        for item in items:
            sheet_items.append(
                ft.Container(
                    content=ft.Text(
                        item.get("jcxm", ""), size=14,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    padding=ft.padding.symmetric(vertical=14),
                    on_click=await _pick(item),
                    ink=True,
                    bgcolor=ft.colors.WHITE,
                    border=ft.border.only(
                        bottom=ft.border.BorderSide(1, ft.colors.GREY_100)
                    ),
                )
            )

        picker_dlg = ft.AlertDialog(
            title=ft.Text("选择检查项", size=16),
            content=ft.Column(
                controls=sheet_items,
                tight=True, spacing=0, width=280,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton("取消", on_click=lambda ev: _close_picker(ev)),
            ],
        )

        async def _close_picker(ev):
            picker_dlg.open = False
            await page.update_async()

        page.dialog = picker_dlg
        picker_dlg.open = True
        await page.update_async()

    # --- 顶部检查项选择栏 ---
    item_selector = ft.Container(
        content=ft.Row(
            controls=[
                item_btn_text,
                ft.Icon(ft.icons.ARROW_DROP_DOWN, color=ft.colors.GREY_500),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=ft.colors.WHITE,
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
        on_click=_show_item_picker,
        ink=True,
        border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200)),
    )

    scroll_content = ft.ListView(
        controls=[
            entries_column,
            ft.Container(
                content=ft.Row([loading_ring], alignment=ft.MainAxisAlignment.CENTER),
                padding=10,
            ),
            load_more_btn,
            empty_widget,
        ],
        expand=True,
    )

    body = ft.Column(
        controls=[item_selector, scroll_content],
        spacing=0, expand=True,
    )

    view = ft.View(
        route=f"/{module_type}/tasks/list",
        appbar=ft.AppBar(title=ft.Text(title), bgcolor=ft.colors.WHITE),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    # 初始加载
    if selected_item[0]:
        await _load_entries(reset=True)

    return view
