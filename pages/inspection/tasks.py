"""电子巡检模块 — 任务列表 + 任务详情 + 检查内容页"""

from __future__ import annotations

from datetime import datetime

import flet as ft

from services import inspection_service as ins
from components.detail_page import detail_section
from components.form_fields import readonly_field, textarea_field
from components.status_badge import status_badge
from components.image_upload import ImageUpload


# Tab: (标签名, 接口 status 值)
_TABS = [
    ("待执行", "1"),
    ("执行中", "3"),
    ("已执行", "2"),
]

# 巡检状态映射
_XJZT_MAP = {"1": "待巡检", "2": "已巡检", "3": "巡检中"}


# ============================================================
# 1. 巡检任务列表页
# ============================================================

async def build_tasks_view(page: ft.Page) -> ft.View:
    """巡检任务列表页 — Tab 切换待执行/执行中/已执行"""

    current_tab = [0]
    current_page_no = [1]
    page_size = 10
    items_data: list[dict] = []
    is_loading = [False]
    search_text = [""]

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

    async def _load_data(reset: bool = False):
        if is_loading[0]:
            return
        is_loading[0] = True
        loading_ring.visible = True
        await page.update_async()

        if reset:
            current_page_no[0] = 1
            items_data.clear()
            list_column.controls.clear()

        try:
            status = _TABS[current_tab[0]][1]
            params: dict = {
                "status": status,
                "pageNo": current_page_no[0],
                "pageSize": page_size,
            }
            if search_text[0]:
                params["name"] = search_text[0]

            result = await ins.get_record_list(params)
            records = result.get("records", []) if isinstance(result, dict) else []
            total = result.get("total", 0) if isinstance(result, dict) else 0

            for item in records:
                items_data.append(item)
                ctrl = _build_task_item(item)

                def _make_click(data):
                    async def _click(e):
                        await page.go_async(f"/inspection/detail?id={data['id']}")
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
        current_page_no[0] += 1
        await _load_data(reset=False)

    def _build_task_item(item: dict) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        item.get("rwmc", ""),
                        size=15, weight=ft.FontWeight.W_500,
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(
                        f"巡检对象类型：{item.get('jcdxlx_dictText', '-')}",
                        size=13, color=ft.colors.GREY_600,
                    ),
                    ft.Text(
                        f"巡检对象：{item.get('jcdx', '-')}",
                        size=13, color=ft.colors.GREY_600,
                    ),
                    ft.Text(
                        f"巡检生产区域：{item.get('xjscqy', '-')}",
                        size=13, color=ft.colors.GREY_600,
                    ),
                    ft.Text(
                        f"创建时间：{item.get('createTime', '-')}",
                        size=12, color=ft.colors.GREY_500,
                    ),
                ],
                spacing=4,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200)),
        )

    # 搜索栏
    async def _on_search(e):
        search_text[0] = e.control.value.strip()
        await _load_data(reset=True)

    search_field = ft.TextField(
        hint_text="搜索",
        prefix_icon=ft.icons.SEARCH,
        on_submit=_on_search,
        border_color=ft.colors.GREY_300,
        focused_border_color=ft.colors.BLUE,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=6),
        text_size=14,
        height=40,
    )
    search_bar = ft.Container(
        content=search_field,
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        bgcolor=ft.colors.WHITE,
    )

    # Tab 栏
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

    body = ft.Column(controls=[search_bar, tabs, scroll_content], spacing=0, expand=True)

    view = ft.View(
        route="/inspection/tasks",
        appbar=ft.AppBar(title=ft.Text("巡检任务"), bgcolor=ft.colors.WHITE),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    await _load_data(reset=True)
    return view


# ============================================================
# 2. 任务详情页（点位列表 + 统计 + 开始巡检/提交/隐患上报）
# ============================================================

async def build_task_detail_view(page: ft.Page, record_id: str) -> ft.View:
    """巡检任务详情页"""

    info: dict = {}
    counts: dict = {}
    points: list[dict] = []
    page_no = [1]
    page_size = 10
    is_bottom = [False]
    is_loading = [False]

    # --- 控件引用 ---
    steps_row = ft.Container()
    info_section = ft.Container()
    stats_section = ft.Container()
    points_column = ft.Column(spacing=8)
    load_more_btn = ft.Container(visible=False)
    start_btn = ft.Container(visible=False)
    appbar_actions: list[ft.Control] = []

    # 提交弹窗状态
    jcjl_field = ft.TextField(
        hint_text="请输入排查结论",
        multiline=True, min_lines=3, max_lines=5,
        border_color=ft.colors.GREY_300,
        text_size=14,
    )
    xczp_upload: ImageUpload | None = None

    # 隐患上报弹窗
    yhbz_field = ft.TextField(
        hint_text="请输入隐患备注",
        multiline=True, min_lines=3, max_lines=5,
        border_color=ft.colors.GREY_300,
        text_size=14,
    )
    report_upload: ImageUpload | None = None

    async def _load_detail():
        nonlocal info, counts
        info = await ins.get_record_detail(record_id)
        try:
            counts = await ins.get_record_count(record_id) or {}
        except Exception:
            counts = {}

    async def _load_points(reset: bool = False):
        nonlocal points
        if is_loading[0]:
            return
        is_loading[0] = True

        if reset:
            page_no[0] = 1
            points.clear()
            points_column.controls.clear()
            is_bottom[0] = False

        try:
            result = await ins.get_item_list({
                "recordId": record_id,
                "pageNo": page_no[0],
                "pageSize": page_size,
            })
            records = result.get("records", []) if isinstance(result, dict) else []
            for item in records:
                points.append(item)
                points_column.controls.append(_build_point_item(item))

            if len(records) < page_size:
                is_bottom[0] = True
                load_more_btn.visible = False
            else:
                load_more_btn.visible = True
                load_more_btn.content = ft.TextButton(
                    "加载更多", on_click=_on_load_more_points,
                    style=ft.ButtonStyle(color=ft.colors.BLUE),
                )
        except Exception:
            pass
        is_loading[0] = False

    async def _on_load_more_points(e):
        page_no[0] += 1
        await _load_points()
        await page.update_async()

    def _build_point_item(item: dict) -> ft.Control:
        xjzt = str(item.get("xjzt", "1"))
        status_text = "已检查" if xjzt == "2" else "待检查"
        status_color = ft.colors.GREEN_700 if xjzt == "2" else ft.colors.BLUE_700

        def _make_click(data):
            async def _click(e):
                import json
                await page.go_async(
                    f"/inspection/content?item={json.dumps(data)}"
                )
            return _click

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                item.get("dwmc", ""),
                                size=14, weight=ft.FontWeight.W_500,
                                expand=True, max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text(status_text, size=13, color=status_color),
                                    ft.Icon(ft.icons.CHEVRON_RIGHT, size=18, color=ft.colors.GREY_400),
                                ],
                                spacing=2,
                                tight=True,
                            ),
                        ],
                    ),
                    ft.Row(controls=[
                        ft.Text(f"点位编号：{item.get('dwbh', '-')}", size=12, color=ft.colors.GREY_600, expand=True),
                        ft.Text(f"所在部门：{item.get('ssbm_dictText', '-')}", size=12, color=ft.colors.GREY_600, expand=True),
                    ]),
                    ft.Text(f"所属设备类型：{item.get('sbsslx_dictText', '-')}", size=12, color=ft.colors.GREY_600),
                    ft.Text(f"所属设备设施：{item.get('sssbss', '-')}", size=12, color=ft.colors.GREY_600),
                ],
                spacing=4,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
            border_radius=8,
            on_click=_make_click(item),
            ink=True,
        )

    def _build_steps(xjzt: str) -> ft.Control:
        """步骤指示器: 任务生成 → 任务中 → 任务完成"""
        step_names = ["任务生成", "任务中", "任务完成"]
        # xjzt: 1=待巡检(step0), 3=巡检中(step1), 2=已巡检(step2)
        active = 0 if xjzt == "1" else (2 if xjzt == "2" else 1)

        controls = []
        for i, name in enumerate(step_names):
            is_active = i <= active
            color = ft.colors.BLUE if is_active else ft.colors.GREY_400
            controls.append(
                ft.Column(
                    controls=[
                        ft.Container(
                            width=28, height=28,
                            border_radius=14,
                            bgcolor=color,
                            alignment=ft.alignment.center,
                            content=ft.Text(str(i + 1), size=12, color=ft.colors.WHITE),
                        ),
                        ft.Text(name, size=11, color=color),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                )
            )
            if i < len(step_names) - 1:
                controls.append(
                    ft.Container(
                        width=40, height=2,
                        bgcolor=ft.colors.BLUE if i < active else ft.colors.GREY_300,
                        margin=ft.margin.only(bottom=16),
                    )
                )

        return ft.Container(
            content=ft.Row(
                controls=controls,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ft.colors.WHITE,
            padding=ft.padding.symmetric(vertical=16),
        )

    def _build_info_section(d: dict) -> ft.Control:
        xjzt = str(d.get("xjzt", "1"))
        fields = [
            readonly_field("巡检生产区域", d.get("xjscqy", "")),
            readonly_field("巡检对象类型", d.get("jcdxlx_dictText", "")),
            readonly_field("计划检查时间", d.get("jhjcsj", "")),
        ]
        if xjzt == "2":
            fields.extend([
                readonly_field("巡检开始时间", d.get("xjkssj", "")),
                readonly_field("巡检结束时间", d.get("xjjssj", "")),
                readonly_field("检查结论", d.get("jcjl", "")),
            ])
        return detail_section("基本信息", fields)

    def _build_stats_section(c: dict) -> ft.Control:
        stats = [
            ("未巡检点位", c.get("toDoItemCount", 0)),
            ("已巡检点位", c.get("finishItemCount", 0)),
            ("未检查内容", c.get("toDoContentCount", 0)),
            ("已检查内容", c.get("finishContentCount", 0)),
        ]
        cards = []
        for label, num in stats:
            cards.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(label, size=13, color=ft.colors.GREY_700),
                            ft.Text(str(num), size=22, color=ft.colors.BLUE, weight=ft.FontWeight.W_500),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4,
                    ),
                    bgcolor=ft.colors.WHITE,
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    expand=True,
                    alignment=ft.alignment.center,
                )
            )
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("巡检统计", size=15, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER),
                    ft.Row(controls=cards[:2], spacing=12),
                    ft.Row(controls=cards[2:], spacing=12),
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
        )

    # --- 操作函数 ---
    async def _start_inspection(e):
        """开始巡检"""
        try:
            await ins.start_record(record_id)
            page.snack_bar = ft.SnackBar(ft.Text("开始巡检"), open=True)
            await _refresh_all()
            await page.update_async()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"操作失败：{ex}"), open=True)
            await page.update_async()

    async def _show_submit_dialog(e):
        """提交巡检任务弹窗"""
        nonlocal xczp_upload
        jcjl_field.value = ""
        xczp_upload = ImageUpload(page, max_count=9)

        async def _confirm(ev):
            if not jcjl_field.value or not jcjl_field.value.strip():
                page.snack_bar = ft.SnackBar(ft.Text("请输入检查结论"), open=True)
                await page.update_async()
                return
            try:
                data = {
                    "id": record_id,
                    "jcjl": jcjl_field.value.strip(),
                    "xczp": ",".join(xczp_upload.uploaded_paths) if xczp_upload else "",
                }
                await ins.check_finish(data)
                page.snack_bar = ft.SnackBar(ft.Text("提交成功"), open=True)
                dlg.open = False
                await page.update_async()
                await _refresh_all()
                await page.update_async()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"提交失败：{ex}"), open=True)
                await page.update_async()

        async def _cancel(ev):
            dlg.open = False
            await page.update_async()

        dlg = ft.AlertDialog(
            title=ft.Text("提交巡检任务"),
            content=ft.Column(
                controls=[
                    ft.Text("* 排查结论", size=14, color=ft.colors.RED),
                    jcjl_field,
                    ft.Text("上传照片", size=14),
                    xczp_upload,
                ],
                spacing=8,
                tight=True,
                width=400,
            ),
            actions=[
                ft.TextButton("取消", on_click=_cancel),
                ft.TextButton("提交", on_click=_confirm),
            ],
        )
        page.dialog = dlg
        dlg.open = True
        await page.update_async()

    async def _show_report_dialog(e):
        """隐患上报弹窗"""
        nonlocal report_upload
        yhbz_field.value = ""
        report_upload = ImageUpload(page, max_count=9)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        async def _confirm(ev):
            if not yhbz_field.value or not yhbz_field.value.strip():
                page.snack_bar = ft.SnackBar(ft.Text("请填写隐患备注"), open=True)
                await page.update_async()
                return
            try:
                data = {
                    "recordId": record_id,
                    "fxsj": now_str,
                    "yhbz": yhbz_field.value.strip(),
                    "xczp": ",".join(report_upload.uploaded_paths) if report_upload else "",
                }
                await ins.epi_report(data)
                page.snack_bar = ft.SnackBar(ft.Text("上报成功"), open=True)
                dlg.open = False
                await page.update_async()
                await _refresh_all()
                await page.update_async()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"上报失败：{ex}"), open=True)
                await page.update_async()

        async def _cancel(ev):
            dlg.open = False
            await page.update_async()

        dlg = ft.AlertDialog(
            title=ft.Text("隐患上报"),
            content=ft.Column(
                controls=[
                    readonly_field("发现时间", now_str),
                    ft.Text("* 隐患备注", size=14, color=ft.colors.RED),
                    yhbz_field,
                    ft.Text("现场照片", size=14),
                    report_upload,
                ],
                spacing=8,
                tight=True,
                width=400,
            ),
            actions=[
                ft.TextButton("取消", on_click=_cancel),
                ft.TextButton("提交", on_click=_confirm),
            ],
        )
        page.dialog = dlg
        dlg.open = True
        await page.update_async()

    async def _refresh_all():
        """刷新详情 + 统计 + 点位列表"""
        await _load_detail()
        xjzt = str(info.get("xjzt", "1"))

        # 更新步骤
        steps_row.content = _build_steps(xjzt).content
        # 更新基本信息
        info_section.content = _build_info_section(info).content
        # 更新统计
        stats_section.content = _build_stats_section(counts).content

        # 更新按钮
        start_btn.visible = xjzt == "1"

        # 更新 AppBar 操作
        appbar_actions.clear()
        if xjzt == "3":
            appbar_actions.append(
                ft.TextButton("提交", on_click=_show_submit_dialog,
                              style=ft.ButtonStyle(color=ft.colors.WHITE))
            )
        if str(info.get("sfyyc", "")) == "1" and str(info.get("yhsbzt", "")) != "2":
            appbar_actions.append(
                ft.TextButton("隐患上报", on_click=_show_report_dialog,
                              style=ft.ButtonStyle(color=ft.colors.WHITE))
            )

        # 点位列表
        if xjzt != "1":
            await _load_points(reset=True)

    # --- 先构建 loading 骨架，立即返回 View ---
    import asyncio

    loading_widget = ft.Container(
        content=ft.ProgressRing(width=32, height=32),
        alignment=ft.alignment.center,
        expand=True,
    )

    start_btn = ft.Container(visible=False)

    points_container = ft.Container(
        content=ft.Column(
            controls=[points_column, load_more_btn],
            spacing=8,
        ),
        padding=ft.padding.symmetric(horizontal=12),
        visible=False,
    )

    body = ft.ListView(
        controls=[
            loading_widget,
            steps_row,
            info_section,
            stats_section,
            points_container,
            start_btn,
        ],
        expand=True,
        padding=ft.padding.only(bottom=20),
    )

    view = ft.View(
        route="/inspection/detail",
        appbar=ft.AppBar(
            title=ft.Text("任务详情"),
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE,
            actions=appbar_actions,
        ),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    # --- 异步加载数据（View 显示后执行） ---
    async def _init_load():
        try:
            await _load_detail()
            xjzt = str(info.get("xjzt", "1"))

            steps_row.content = _build_steps(xjzt).content
            info_section.content = _build_info_section(info).content
            stats_section.content = _build_stats_section(counts).content

            if xjzt != "1":
                points_container.visible = True
                await _load_points(reset=True)

            # 开始巡检按钮
            if xjzt == "1":
                start_btn.content = ft.ElevatedButton(
                    "开始巡检", on_click=_start_inspection,
                    bgcolor=ft.colors.BLUE, color=ft.colors.WHITE,
                    width=200,
                )
                start_btn.alignment = ft.alignment.center
                start_btn.padding = ft.padding.only(top=40)
                start_btn.visible = True

            # AppBar 动作按钮
            appbar_actions.clear()
            if xjzt == "3":
                appbar_actions.append(
                    ft.TextButton("提交", on_click=_show_submit_dialog,
                                  style=ft.ButtonStyle(color=ft.colors.WHITE))
                )
            if str(info.get("sfyyc", "")) == "1" and str(info.get("yhsbzt", "")) != "2":
                appbar_actions.append(
                    ft.TextButton("隐患上报", on_click=_show_report_dialog,
                                  style=ft.ButtonStyle(color=ft.colors.WHITE))
                )
        except Exception as ex:
            loading_widget.content = ft.Column(
                controls=[
                    ft.Icon(ft.icons.ERROR_OUTLINE, size=48, color=ft.colors.RED_300),
                    ft.Text(f"加载失败：{ex}", size=14, color=ft.colors.GREY_600),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            )

        loading_widget.visible = False
        await page.update_async()

    asyncio.ensure_future(_init_load())
    return view


# ============================================================
# 3. 检查内容页（逐项填写检查结果 + 签到）
# ============================================================

async def build_content_view(page: ft.Page, item_data: dict) -> ft.View:
    """检查内容页 — 检查项列表 + NFC/扫码签到 + 提交点位"""

    record_item_id = item_data.get("id", "")
    point_info = dict(item_data)  # 点位信息（含 qdsj, xjzt 等）

    content_list: list[dict] = []
    page_no = [1]
    page_size = 10
    is_bottom = [False]
    is_loading = [False]

    list_column = ft.Column(spacing=8)
    load_more_btn = ft.Container(visible=False)

    # 签到状态
    sign_status = ft.Container()

    async def _load_contents(reset: bool = False):
        nonlocal content_list
        if is_loading[0]:
            return
        is_loading[0] = True

        if reset:
            page_no[0] = 1
            content_list.clear()
            list_column.controls.clear()
            is_bottom[0] = False

        try:
            result = await ins.get_content_list({
                "recordItemId": record_item_id,
                "pageNo": page_no[0],
                "pageSize": page_size,
            })
            records = result.get("records", []) if isinstance(result, dict) else []
            for item in records:
                content_list.append(item)
                list_column.controls.append(_build_content_item(item))

            if len(records) < page_size:
                is_bottom[0] = True
                load_more_btn.visible = False
            else:
                load_more_btn.visible = True
                load_more_btn.content = ft.TextButton(
                    "加载更多", on_click=_on_load_more,
                    style=ft.ButtonStyle(color=ft.colors.BLUE),
                )
        except Exception:
            pass
        is_loading[0] = False

    async def _on_load_more(e):
        page_no[0] += 1
        await _load_contents()
        await page.update_async()

    def _build_content_item(item: dict) -> ft.Control:
        """构建单个检查内容项"""
        sfyc = item.get("sfyc")  # None=未检查, 0=正常, 1=异常
        jczt_text = item.get("jczt_dictText", "")
        sfyc_text = item.get("sfyc_dictText", "")

        status_controls = [
            ft.Text(
                jczt_text,
                size=13,
                color=ft.colors.BLUE_700 if str(item.get("jczt", "")) == "1" else ft.colors.GREEN_700,
            ),
        ]
        if sfyc is not None:
            sfyc_color = ft.colors.GREEN_700 if sfyc == 0 else ft.colors.RED_700
            status_controls.append(ft.Text(sfyc_text, size=13, color=sfyc_color))

        def _make_click(data):
            async def _click(e):
                if data.get("sfyc") is not None:
                    return  # 已检查的不能再点
                await _show_check_dialog(data)
            return _click

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(item.get("jcnr", ""), size=14, color=ft.colors.BLACK87),
                    ft.Row(
                        controls=status_controls,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=6,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
            border_radius=6,
            on_click=_make_click(item),
            ink=True,
        )

    async def _show_check_dialog(item: dict):
        """弹窗显示检查详情，选择正常/异常"""

        async def _submit_result(sfyc: int):
            try:
                await ins.submit_content({
                    "sfyc": sfyc,
                    "contentId": item["id"],
                })
                page.snack_bar = ft.SnackBar(ft.Text("操作成功"), open=True)
                dlg.open = False
                await page.update_async()
                # 刷新列表
                await _load_contents(reset=True)
                await page.update_async()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"操作失败：{ex}"), open=True)
                await page.update_async()

        async def _on_normal(ev):
            await _submit_result(0)

        async def _on_abnormal(ev):
            await _submit_result(1)

        dlg = ft.AlertDialog(
            title=ft.Text("检查详情"),
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text(item.get("jcnr", ""), size=14),
                        padding=ft.padding.all(12),
                        border=ft.border.all(1, ft.colors.GREY_300),
                        border_radius=6,
                    ),
                    ft.Container(
                        content=ft.Text(item.get("jcbz", "") or "", size=13, color=ft.colors.GREY_600),
                        padding=ft.padding.all(12),
                        border=ft.border.all(1, ft.colors.GREY_300),
                        border_radius=6,
                        visible=bool(item.get("jcbz")),
                    ),
                ],
                spacing=8,
                tight=True,
                width=350,
            ),
            actions=[
                ft.TextButton("异常", on_click=_on_abnormal,
                              style=ft.ButtonStyle(color=ft.colors.RED)),
                ft.TextButton("正常", on_click=_on_normal,
                              style=ft.ButtonStyle(color=ft.colors.GREEN)),
            ],
        )
        page.dialog = dlg
        dlg.open = True
        await page.update_async()

    async def _do_sign_in():
        """执行签到"""
        try:
            await ins.sign_in(record_item_id)
            point_info["qdsj"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            page.snack_bar = ft.SnackBar(ft.Text("签到成功"), open=True)
            _update_sign_status()
            await page.update_async()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"签到失败：{ex}"), open=True)
            await page.update_async()

    async def _on_manual_sign(e):
        """手动签到（替代 NFC/扫码）"""
        await _do_sign_in()

    async def _submit_point(e):
        """提交点位检查结果"""
        # 检查是否所有内容都已检查
        unchecked = [c for c in content_list if c.get("sfyc") is None]
        if unchecked:
            page.snack_bar = ft.SnackBar(ft.Text("有未检查内容，请继续检查！"), open=True)
            await page.update_async()
            return

        # 确认弹窗
        async def _confirm(ev):
            try:
                await ins.submit_item(record_item_id)
                page.snack_bar = ft.SnackBar(ft.Text("提交成功"), open=True)
                confirm_dlg.open = False
                await page.update_async()
                # 返回上一页
                page.views.pop()
                await page.update_async()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"提交失败：{ex}"), open=True)
                await page.update_async()

        async def _cancel(ev):
            confirm_dlg.open = False
            await page.update_async()

        confirm_dlg = ft.AlertDialog(
            title=ft.Text("提交点位检查结果"),
            content=ft.Text("是否确认提交点位检查结果，提交后无法修改"),
            actions=[
                ft.TextButton("取消", on_click=_cancel),
                ft.TextButton("确认", on_click=_confirm),
            ],
        )
        page.dialog = confirm_dlg
        confirm_dlg.open = True
        await page.update_async()

    def _update_sign_status():
        """更新签到区域显示"""
        has_signed = bool(point_info.get("qdsj"))
        xjzt = point_info.get("xjzt")

        if has_signed:
            if xjzt:
                msg = "巡检点已完成！"
            else:
                msg = "已签到，请提交！"
            sign_status.content = ft.ElevatedButton(
                msg, disabled=True,
                bgcolor=ft.colors.BLUE, color=ft.colors.WHITE,
            )
        else:
            # TODO: Flet 不支持 NFC 扫描和二维码扫描，使用手动签到替代
            # 如需 NFC 或扫码签到，需接入原生插件或外部设备
            sign_status.content = ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.icons.QR_CODE_SCANNER, size=60, color=ft.colors.GREY_500),
                        alignment=ft.alignment.center,
                        on_click=_on_manual_sign,
                        ink=True,
                        tooltip="TODO: 扫码签到（Flet 暂不支持摄像头扫码，点击此处手动签到）",
                    ),
                    ft.ElevatedButton(
                        "手动签到",
                        icon=ft.icons.CHECK_CIRCLE_OUTLINE,
                        on_click=_on_manual_sign,
                        bgcolor=ft.colors.BLUE,
                        color=ft.colors.WHITE,
                        tooltip="替代 NFC/扫码签到",
                    ),
                    ft.Text(
                        "TODO: NFC 签到和二维码扫码签到需接入原生能力",
                        size=11, color=ft.colors.GREY_500,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            )
        sign_status.padding = ft.padding.symmetric(vertical=20, horizontal=40)
        sign_status.alignment = ft.alignment.center

    # --- 初始化 ---
    _update_sign_status()
    await _load_contents(reset=True)

    # AppBar 操作按钮
    appbar_actions = []
    xjzt = point_info.get("xjzt")
    if str(xjzt) != "2":
        appbar_actions.append(
            ft.TextButton("提交", on_click=_submit_point,
                          style=ft.ButtonStyle(color=ft.colors.WHITE))
        )

    body = ft.ListView(
        controls=[
            sign_status,
            ft.Container(
                content=ft.Column(controls=[list_column, load_more_btn], spacing=8),
                padding=ft.padding.symmetric(horizontal=12),
            ),
        ],
        expand=True,
        padding=ft.padding.only(bottom=20),
    )

    return ft.View(
        route="/inspection/content",
        appbar=ft.AppBar(
            title=ft.Text("任务详情"),
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE,
            actions=appbar_actions,
        ),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )
