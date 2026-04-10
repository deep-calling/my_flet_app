"""学习资料 + 线上培训任务 — 列表页与学习详情"""

from __future__ import annotations

import asyncio

import flet as ft

from services import train_service as ts
from components.status_badge import status_badge
from components.detail_page import detail_section
from components.form_fields import readonly_field
from config import app_config


# ============================================================
# 学习资料列表
# ============================================================

async def build_online_learn_view(page: ft.Page) -> ft.View:
    """学习资料列表页"""

    current_page_no = [1]
    page_size = 10
    items_data: list[dict] = []
    is_loading = [False]

    # 筛选状态
    file_type_val = [""]
    type_val = [""]
    file_type_options: list[dict] = []
    type_options: list[dict] = []

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

    # 加载字典
    try:
        ft_dict = await ts.get_file_type_dict()
        if isinstance(ft_dict, list):
            file_type_options.extend(
                [{"text": d.get("text", d.get("title", "")), "value": str(d.get("value", ""))} for d in ft_dict]
            )
    except Exception:
        pass
    try:
        t_dict = await ts.get_type_dict()
        if isinstance(t_dict, list):
            type_options.extend(
                [{"text": d.get("text", d.get("title", "")), "value": str(d.get("value", ""))} for d in t_dict]
            )
    except Exception:
        pass

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
            params: dict = {
                "pageNo": current_page_no[0],
                "pageSize": page_size,
            }
            if file_type_val[0]:
                params["fileType"] = file_type_val[0]
            if type_val[0]:
                params["type"] = type_val[0]

            result = await ts.get_online_learning_list(params)
            records = result.get("records", []) if isinstance(result, dict) else []
            total = result.get("total", 0) if isinstance(result, dict) else 0

            for item in records:
                items_data.append(item)
                ctrl = _build_item(item)

                def _make_click(data):
                    async def _click(e):
                        await page.go_async(
                            f"/train/learn/detail?id={data.get('id', '')}"
                        )
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

    def _build_item(item: dict) -> ft.Control:
        flag = str(item.get("flag", "0"))
        learn_text = "已学习" if flag == "1" else "未学习"
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(controls=[
                        ft.Text(
                            item.get("zlbt", ""),
                            size=15, weight=ft.FontWeight.W_500,
                            expand=True, max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        status_badge(learn_text),
                    ]),
                    ft.Text(
                        f"类别：{item.get('sslb_dictText', '-')}  |  类型：{item.get('wjlx_dictText', '-')}",
                        size=13, color=ft.colors.GREY_600,
                    ),
                    ft.Text(
                        item.get("jcjj", "") or "暂无简介",
                        size=12, color=ft.colors.GREY_500,
                        max_lines=2, overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                spacing=4,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200)),
        )

    # 筛选栏
    async def _on_file_type_change(e):
        file_type_val[0] = e.control.value or ""
        await _load_data(reset=True)

    async def _on_type_change(e):
        type_val[0] = e.control.value or ""
        await _load_data(reset=True)

    filter_controls: list[ft.Control] = []
    if file_type_options:
        filter_controls.append(ft.Dropdown(
            hint_text="所属类别",
            options=[ft.dropdown.Option(key=o["value"], text=o["text"]) for o in file_type_options],
            on_change=_on_file_type_change,
            border_color=ft.colors.GREY_300,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            text_size=13, height=38, expand=True,
        ))
    if type_options:
        filter_controls.append(ft.Dropdown(
            hint_text="文件类型",
            options=[ft.dropdown.Option(key=o["value"], text=o["text"]) for o in type_options],
            on_change=_on_type_change,
            border_color=ft.colors.GREY_300,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            text_size=13, height=38, expand=True,
        ))

    filter_bar = ft.Container(
        content=ft.Row(controls=filter_controls, spacing=8),
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        bgcolor=ft.colors.WHITE,
    ) if filter_controls else ft.Container(visible=False)

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

    body = ft.Column(controls=[filter_bar, scroll_content], spacing=0, expand=True)

    view = ft.View(
        route="/train/materials",
        appbar=ft.AppBar(title=ft.Text("学习资料"), bgcolor=ft.colors.WHITE),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    await _load_data(reset=True)
    return view


# ============================================================
# 学习详情页（文件查看 — 打开链接）
# ============================================================

async def build_learn_detail_view(page: ft.Page, material_id: str) -> ft.View:
    """学习详情页：显示文件列表，点击打开链接查看；记录学习时长"""

    study_seconds = [0]
    timer_running = [False]
    timer_task = [None]
    selected_file = [None]

    # 控件引用
    timer_text = ft.Text("学习时长：0 秒", size=14)
    start_btn_text = ft.Text("开始学习")
    file_list_column = ft.Column(spacing=0)

    info_data = [{}]

    async def _load_detail():
        """加载学习资料详情"""
        try:
            params: dict = {"pageNo": 1, "pageSize": 100}
            result = await ts.get_online_learning_list(params)
            records = result.get("records", []) if isinstance(result, dict) else []
            for r in records:
                if r.get("id") == material_id:
                    info_data[0] = r
                    break
            _build_file_list()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"加载失败：{ex}"), open=True)
        await page.update_async()

    def _build_file_list():
        file_list_column.controls.clear()
        files = info_data[0].get("files", [])
        url = info_data[0].get("url", "")
        if not files and url:
            # 单文件模式
            files = [{"name": info_data[0].get("zlbt", "文件"), "path": url}]
        for f in files:
            def _make_open(file_info):
                async def _open(e):
                    selected_file[0] = file_info
                    # 打开文件链接
                    file_url = f"{app_config.host}{file_info.get('path', '')}"
                    await page.launch_url_async(file_url)
                return _open

            file_list_column.controls.append(
                ft.Container(
                    content=ft.ListTile(
                        leading=ft.Icon(ft.icons.DESCRIPTION, color=ft.colors.BLUE),
                        title=ft.Text(f.get("name", f.get("text", "文件")), size=14),
                        trailing=ft.Icon(ft.icons.OPEN_IN_NEW, size=18, color=ft.colors.GREY_500),
                        on_click=_make_open(f),
                    ),
                    bgcolor=ft.colors.WHITE,
                    border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200)),
                )
            )

    async def _timer_loop():
        while timer_running[0]:
            await asyncio.sleep(1)
            study_seconds[0] += 1
            mins = study_seconds[0] // 60
            secs = study_seconds[0] % 60
            timer_text.value = f"学习时长：{mins}分{secs}秒"
            try:
                await page.update_async()
            except Exception:
                break

    async def _toggle_timer(e):
        if timer_running[0]:
            # 停止
            timer_running[0] = False
            start_btn_text.value = "继续学习"
        else:
            # 开始
            timer_running[0] = True
            start_btn_text.value = "暂停学习"
            timer_task[0] = asyncio.create_task(_timer_loop())
        await page.update_async()

    async def _save_record(e):
        if study_seconds[0] <= 0:
            page.snack_bar = ft.SnackBar(ft.Text("请先开始学习"), open=True)
            await page.update_async()
            return
        timer_running[0] = False
        try:
            data = {
                "materialId": material_id,
                "xs": study_seconds[0],
            }
            if selected_file[0]:
                data["zl"] = selected_file[0].get("path", "")
            await ts.submit_learning_record(data)
            page.snack_bar = ft.SnackBar(ft.Text("学习记录已保存"), open=True)
            await page.update_async()
            page.views.pop()
            await page.update_async()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"保存失败：{ex}"), open=True)
            await page.update_async()

    await _load_detail()

    # 页面内容
    content = ft.Column(
        controls=[
            detail_section("资料信息", [
                readonly_field("资料标题", info_data[0].get("zlbt", "")),
                readonly_field("类别", info_data[0].get("sslb_dictText", "")),
                readonly_field("简介", info_data[0].get("jcjj", "") or "暂无"),
            ]),
            detail_section("文件列表", [file_list_column]),
            ft.Container(
                content=ft.Row(
                    controls=[
                        timer_text,
                        ft.ElevatedButton(content=start_btn_text, on_click=_toggle_timer),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
                bgcolor=ft.colors.WHITE,
            ),
        ],
        spacing=0,
    )

    body = ft.Column(
        controls=[
            ft.ListView(controls=[content], expand=True, padding=0),
            ft.Container(
                content=ft.Row(controls=[
                    ft.ElevatedButton(
                        text="保存学习记录",
                        on_click=_save_record,
                        bgcolor=ft.colors.BLUE,
                        color=ft.colors.WHITE,
                        expand=True,
                    ),
                ], spacing=12),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                bgcolor=ft.colors.WHITE,
                border=ft.border.only(top=ft.border.BorderSide(1, ft.colors.GREY_200)),
            ),
        ],
        spacing=0,
        expand=True,
    )

    return ft.View(
        route="/train/learn/detail",
        appbar=ft.AppBar(title=ft.Text("学习详情"), bgcolor=ft.colors.WHITE),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )


# ============================================================
# 线上培训任务列表
# ============================================================

async def build_training_task_view(page: ft.Page) -> ft.View:
    """线上培训任务列表"""

    current_page_no = [1]
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
            result = await ts.get_training_task_list({
                "pageNo": current_page_no[0],
                "pageSize": page_size,
            })
            records = result.get("records", []) if isinstance(result, dict) else []
            total = result.get("total", 0) if isinstance(result, dict) else 0

            for item in records:
                items_data.append(item)
                ctrl = _build_item(item)

                def _make_click(data):
                    async def _click(e):
                        await page.go_async(f"/train/task/detail?id={data.get('id', '')}")
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

    def _build_item(item: dict) -> ft.Control:
        gdsc = item.get("gdsc", 0)
        yxxsc = item.get("yxxsc", 0)
        learned_mins = round(float(yxxsc) / 60.0, 2) if yxxsc else 0
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        item.get("zlbt", ""),
                        size=15, weight=ft.FontWeight.W_500,
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(
                        f"培训计划：{item.get('planId_dictText', '-')}",
                        size=13, color=ft.colors.GREY_600,
                    ),
                    ft.Row(controls=[
                        ft.Text(f"规定时长：{gdsc}分钟", size=12, color=ft.colors.GREY_500, expand=True),
                        ft.Text(f"已学：{learned_mins}分钟", size=12, color=ft.colors.BLUE),
                    ]),
                    ft.Text(
                        f"完成情况：{item.get('wcqk_dictText', '-')}",
                        size=12, color=ft.colors.GREY_500,
                    ),
                ],
                spacing=4,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200)),
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

    body = ft.Column(controls=[scroll_content], spacing=0, expand=True)

    view = ft.View(
        route="/train/task",
        appbar=ft.AppBar(title=ft.Text("线上培训"), bgcolor=ft.colors.WHITE),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    await _load_data(reset=True)
    return view
