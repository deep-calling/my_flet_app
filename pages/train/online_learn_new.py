"""线上培训（新版）— 列表 + 学习详情（含倒计时）"""

from __future__ import annotations

import asyncio

import flet as ft

from services import train_service as ts
from components.detail_page import detail_section
from components.form_fields import readonly_field
from config import app_config


# ============================================================
# 新版线上培训列表
# ============================================================

async def build_online_learn_new_view(page: ft.Page) -> ft.View:
    """新版线上培训列表"""

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
            params: dict = {
                "pageNo": current_page_no[0],
                "pageSize": page_size,
            }
            if search_text[0]:
                params["jhmc"] = search_text[0]

            result = await ts.get_learn_list_new(params)
            records = result.get("records", []) if isinstance(result, dict) else []
            total = result.get("total", 0) if isinstance(result, dict) else 0

            for item in records:
                items_data.append(item)
                ctrl = _build_item(item)

                def _make_click(data):
                    async def _click(e):
                        await page.go_async(f"/train/learn_new/detail?id={data.get('id', '')}")
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

    async def _on_search(e):
        search_text[0] = e.control.value.strip()
        await _load_data(reset=True)

    def _build_item(item: dict) -> ft.Control:
        gdsc = item.get("gdsc", 0)
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        item.get("jhmc", ""),
                        size=15, weight=ft.FontWeight.W_500,
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(
                        f"培训资料：{item.get('fjzl', '-')}",
                        size=13, color=ft.colors.GREY_600,
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(f"规定时长：{gdsc} 分钟", size=12, color=ft.colors.GREY_500),
                ],
                spacing=4,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200)),
        )

    search_field = ft.TextField(
        hint_text="搜索培训名称",
        prefix_icon=ft.icons.SEARCH,
        on_submit=_on_search,
        border_color=ft.colors.GREY_300,
        focused_border_color=ft.colors.BLUE,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=6),
        text_size=14, height=40,
    )
    search_bar = ft.Container(
        content=search_field,
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        bgcolor=ft.colors.WHITE,
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

    body = ft.Column(controls=[search_bar, scroll_content], spacing=0, expand=True)

    view = ft.View(
        route="/train/online",
        appbar=ft.AppBar(title=ft.Text("线上培训"), bgcolor=ft.colors.WHITE),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    await _load_data(reset=True)
    return view


# ============================================================
# 新版学习详情页（倒计时模式）
# ============================================================

async def build_learn_detail_new_view(page: ft.Page, record_id: str) -> ft.View:
    """新版学习详情页：倒计时学习，暂存/保存"""

    info = [{}]
    remaining_secs = [0]  # 剩余秒数（倒计时）
    start_status = [0]  # 0=未开始, 1=学习中, 2=暂停
    timer_running = [False]
    selected_file = [None]

    timer_text = ft.Text("00:00:00", size=24, weight=ft.FontWeight.BOLD)
    btn_text = ft.Text("开始学习")
    file_list_column = ft.Column(spacing=0)

    def _format_time(secs: int) -> str:
        h = secs // 3600
        m = (secs % 3600) // 60
        s = secs % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    async def _load():
        try:
            result = await ts.query_learn_record(record_id)
            if isinstance(result, dict):
                info[0] = result
                gdsc = int(result.get("gdsc", 0))
                yxxsc = int(result.get("yxxsc", 0))
                remaining_secs[0] = max(gdsc * 60 - yxxsc, 0)
                timer_text.value = _format_time(remaining_secs[0])
                _build_file_list()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"加载失败：{ex}"), open=True)
        await page.update_async()

    def _build_file_list():
        file_list_column.controls.clear()
        pxzl = info[0].get("pxzl", "")
        if not pxzl:
            return
        file_paths = [p.strip() for p in pxzl.split(",") if p.strip()]
        for fp in file_paths:
            name = fp.replace("temp/", "").split("/")[-1]

            def _make_open(path, fname):
                async def _open(e):
                    selected_file[0] = {"path": path, "name": fname}
                    file_url = f"{app_config.host}/{path}" if not path.startswith("/") else f"{app_config.host}{path}"
                    await page.launch_url_async(file_url)
                return _open

            file_list_column.controls.append(
                ft.Container(
                    content=ft.ListTile(
                        leading=ft.Icon(ft.icons.DESCRIPTION, color=ft.colors.BLUE),
                        title=ft.Text(name, size=14),
                        trailing=ft.Icon(ft.icons.OPEN_IN_NEW, size=18, color=ft.colors.GREY_500),
                        on_click=_make_open(fp, name),
                    ),
                    bgcolor=ft.colors.WHITE,
                    border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200)),
                )
            )

    async def _timer_loop():
        while timer_running[0] and remaining_secs[0] > 0:
            await asyncio.sleep(1)
            remaining_secs[0] -= 1
            timer_text.value = _format_time(remaining_secs[0])
            try:
                await page.update_async()
            except Exception:
                break
        if remaining_secs[0] <= 0:
            timer_running[0] = False
            start_status[0] = 0
            btn_text.value = "学习完成"
            timer_text.value = "00:00:00"
            try:
                await page.update_async()
            except Exception:
                pass

    async def _toggle_timer(e):
        if remaining_secs[0] <= 0:
            return
        if start_status[0] == 0:
            # 开始
            start_status[0] = 1
            timer_running[0] = True
            btn_text.value = "暂停学习"
            asyncio.create_task(_timer_loop())
        elif start_status[0] == 1:
            # 暂停
            start_status[0] = 2
            timer_running[0] = False
            btn_text.value = "继续学习"
        elif start_status[0] == 2:
            # 继续
            start_status[0] = 1
            timer_running[0] = True
            btn_text.value = "暂停学习"
            asyncio.create_task(_timer_loop())
        await page.update_async()

    async def _temp_save(e):
        """暂存进度"""
        timer_running[0] = False
        start_status[0] = 2
        btn_text.value = "继续学习"
        try:
            await ts.temp_save_learn_record({
                "id": record_id,
                "yxxsc": remaining_secs[0],
            })
            page.snack_bar = ft.SnackBar(ft.Text("已暂存"), open=True)
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"暂存失败：{ex}"), open=True)
        await page.update_async()

    async def _save(e):
        """保存（需倒计时归零）"""
        timer_running[0] = False
        if remaining_secs[0] > 0:
            # 弹窗提示
            async def _close_dlg(ev):
                dlg.open = False
                await page.update_async()

            dlg = ft.AlertDialog(
                title=ft.Text("提示"),
                content=ft.Text("规定的学时未完成，无法保存。"),
                actions=[ft.TextButton("确定", on_click=_close_dlg)],
            )
            page.dialog = dlg
            dlg.open = True
            await page.update_async()
            return

        try:
            await ts.save_learn_record(info[0])
            page.snack_bar = ft.SnackBar(ft.Text("保存成功"), open=True)
            await page.update_async()
            page.views.pop()
            await page.update_async()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"保存失败：{ex}"), open=True)
            await page.update_async()

    await _load()

    # 自动开始（如果有历史进度）
    if info[0].get("yxxsc") and remaining_secs[0] > 0:
        start_status[0] = 1
        timer_running[0] = True
        btn_text.value = "暂停学习"
        asyncio.create_task(_timer_loop())

    content = ft.Column(
        controls=[
            # 倒计时区域
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("剩余学习时间", size=14, color=ft.colors.GREY_600),
                        timer_text,
                        ft.ElevatedButton(content=btn_text, on_click=_toggle_timer),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                padding=20,
                bgcolor=ft.colors.WHITE,
                alignment=ft.alignment.center,
                margin=ft.margin.only(bottom=10),
            ),
            detail_section("培训信息", [
                readonly_field("培训名称", info[0].get("jhmc", info[0].get("pxjhmc", ""))),
                readonly_field("规定时长", f"{info[0].get('gdsc', 0)} 分钟"),
            ]),
            detail_section("培训资料", [file_list_column]),
        ],
        spacing=0,
    )

    body = ft.Column(
        controls=[
            ft.ListView(controls=[content], expand=True, padding=0),
            ft.Container(
                content=ft.Row(controls=[
                    ft.OutlinedButton(text="暂存", on_click=_temp_save, expand=True),
                    ft.ElevatedButton(
                        text="保存", on_click=_save,
                        bgcolor=ft.colors.BLUE, color=ft.colors.WHITE, expand=True,
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
        route="/train/learn_new/detail",
        appbar=ft.AppBar(title=ft.Text("学习详情"), bgcolor=ft.colors.WHITE),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )
