"""作业票列表页 — 三个 Tab（待处理/已完成/预约待完善）+ 类型筛选"""

from __future__ import annotations

import traceback
from typing import Any

import flet as ft

from components.scroll_helper import apply_no_bounce

from pages.ticket.config import TICKET_TYPES, get_config_by_type_value
from services import ticket_service as svc
from utils.app_state import app_state


# 列表 tab 定义
_TABS = [
    {"label": "待处理", "value": "1"},
    {"label": "已完成", "value": "2"},
    {"label": "预约待完善", "value": "3"},
]


def _status_text(item: dict) -> tuple[str, str]:
    """根据后端字段返回 (状态文本, 颜色)"""
    status = item.get("status")
    step = item.get("step", 0)
    acceptance = item.get("acceptanceStatus")

    if status is False or status == "false":
        return "待完善", ft.colors.GREY_500
    if str(status) == "4":
        return "已作废", ft.colors.GREY_500
    if step and int(step) < 5:
        return "审批中", "#789262"
    if step and int(step) == 5:
        approval = item.get("approvalStatus")
        if str(approval) == "1":
            begin = item.get("beginTime") or item.get("dhBeginTime")
            pause = item.get("pauseStatus")
            if not begin:
                return "可开始", "#00E500"
            if str(pause) == "1":
                return "作业暂停", "#FFA500"
            if str(item.get("completeStatus")) == "1":
                return "作业待验收", "#00E500"
            return "作业中", "#00E500"
    if step and int(step) == 6 and str(acceptance) == "2":
        return "已完成", ft.colors.BLACK
    return "处理中", ft.colors.BLUE


def _responsible_person(item: dict) -> str:
    """获取作业负责人显示文本"""
    type_val = str(item.get("type", ""))
    if type_val == "7":
        return item.get("zyzh_dictText", "") or ""
    if type_val == "11":
        return item.get("zydwfzr_dictText", "") or ""
    return item.get("zyfzr_dictText", "") or ""


async def build_ticket_list_page(page: ft.Page) -> ft.View:
    """构建作业票列表页"""

    # --- 状态 ---
    current_tab = ["1"]
    current_type_value = ["3"]  # 默认动火
    page_no = [1]
    page_size = 10
    items_data: list[dict] = []
    is_loading = [False]
    type_options: list[dict] = []

    # --- 控件 ---
    list_column = ft.Column(spacing=0)
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
    type_dropdown_text = ft.Text("动火作业", size=14)

    # --- 加载数据 ---
    async def _load(reset: bool = False):
        if is_loading[0]:
            return
        is_loading[0] = True
        loading_ring.visible = True
        try:
            await page.update_async()
        except Exception:
            pass

        if reset:
            page_no[0] = 1
            items_data.clear()
            list_column.controls.clear()

        try:
            cfg = get_config_by_type_value(current_type_value[0])
            username = app_state.user_info.get("username", "")

            if current_tab[0] == "3":
                # 预约待完善 → 作业申请列表
                result = await svc.zysq_sq_list({
                    "column": "createTime",
                    "order": "desc",
                    "field": "id,",
                    "zylx": current_type_value[0] or "3",
                    "sqStatus": 2,
                    "pageNo": page_no[0],
                    "pageSize": page_size,
                })
            else:
                api_prefix = cfg.api_prefix if cfg else "/jeecg-boot/app/ticket"
                result = await svc.ticket_list(api_prefix, {
                    "type": current_tab[0],
                    "workType": current_type_value[0],
                    "username": username,
                    "pageNo": page_no[0],
                    "pageSize": page_size,
                })

            records = result.get("records", []) if isinstance(result, dict) else []
            total = result.get("total", 0) if isinstance(result, dict) else 0
            print(f"[ticket_list] tab={current_tab[0]} workType={current_type_value[0]} "
                  f"pageNo={page_no[0]} → records={len(records)} total={total}")

            for item in records:
                items_data.append(item)
                list_column.controls.append(_build_item(item))

            has_more = len(items_data) < total
            load_more_btn.visible = has_more
            if has_more:
                load_more_btn.content = ft.TextButton("加载更多", on_click=_on_load_more)
            empty_widget.visible = len(items_data) == 0

        except Exception as ex:
            traceback.print_exc()
            print(f"[ticket_list] 加载失败：{ex}")
            empty_widget.visible = len(items_data) == 0
            try:
                page.snack_bar = ft.SnackBar(ft.Text(f"加载失败：{ex}"), open=True)
            except Exception:
                pass

        is_loading[0] = False
        loading_ring.visible = False
        try:
            await page.update_async()
        except Exception:
            pass

    async def _on_load_more(e):
        page_no[0] += 1
        await _load(reset=False)

    # --- 构建列表项 ---
    def _build_item(item: dict) -> ft.Control:
        status_txt, status_color = _status_text(item)
        ticket_no = item.get("zyzbh", "")
        sqdw = item.get("sqdw_dictText", "")
        sqr = item.get("sqr_dictText", "")
        fzr = _responsible_person(item)

        def _make_click(data):
            async def _click(e):
                await _go_detail(data)
            return _click

        card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(status_txt, size=12, color=ft.colors.WHITE),
                                bgcolor=status_color,
                                border_radius=4,
                                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                            ),
                            ft.Text(ticket_no, size=13, weight=ft.FontWeight.W_500, expand=True),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Row(
                        controls=[
                            ft.Text(f"申请单位: {sqdw}", size=12, color=ft.colors.GREY_600, expand=True),
                            ft.Text(f"申请人: {sqr}", size=12, color=ft.colors.GREY_600),
                        ],
                    ),
                    ft.Text(f"作业负责人: {fzr}", size=12, color=ft.colors.GREY_600)
                    if fzr else ft.Container(),
                ],
                spacing=6,
            ),
            padding=ft.padding.all(12),
            bgcolor=ft.colors.WHITE,
            border_radius=8,
            margin=ft.margin.symmetric(horizontal=12, vertical=4),
            on_click=_make_click(item),
            ink=True,
        )
        return card

    # --- 点击进入详情 ---
    async def _go_detail(item: dict):
        ticket_id = item.get("id", "")
        type_val = str(item.get("type", current_type_value[0]))
        has_ysr = bool(item.get("ysr"))

        if has_ysr:
            page.go(f"/ticket/detail?id={ticket_id}&type={type_val}")
        else:
            page.go(f"/ticket/add?type={type_val}&sq={ticket_id}")

    # --- Tab 切换 ---
    async def _on_tab_change(e):
        current_tab[0] = _TABS[e.control.selected_index]["value"]
        await _load(reset=True)

    # --- 类型选择 ---
    async def _show_type_picker(e):
        def _make_select(val, txt, sheet):
            async def _select(ev):
                current_type_value[0] = val
                type_dropdown_text.value = txt
                sheet.open = False
                await page.update_async()
                await _load(reset=True)
            return _select

        bs = ft.BottomSheet(content=ft.Container(), open=True)
        options = []
        for t in type_options:
            options.append(
                ft.ListTile(
                    title=ft.Text(t["text"]),
                    on_click=_make_select(t["value"], t["text"], bs),
                )
            )
        bs.content = ft.Container(
            content=ft.Column(options, tight=True, scroll=ft.ScrollMode.AUTO),
            padding=16,
            height=400,
        )
        page.overlay.append(bs)
        await page.update_async()

    # --- 初始化类型列表 ---
    async def _init_types():
        nonlocal type_options
        try:
            result = await svc.get_dict_work_type()
            if isinstance(result, list):
                type_options = [{"text": r.get("text", ""), "value": r.get("value", "")} for r in result]
        except Exception:
            pass

    # --- 新增按钮 ---
    async def _on_add(e):
        page.go(f"/ticket/add?type={current_type_value[0]}")

    # --- 组装页面 ---
    tabs = ft.Tabs(
        selected_index=0,
        on_change=_on_tab_change,
        tabs=[ft.Tab(text=t["label"]) for t in _TABS],
        label_color=ft.colors.BLUE,
        unselected_label_color=ft.colors.GREY_600,
        indicator_color=ft.colors.BLUE,
        divider_color=ft.colors.GREY_200,
    )

    type_selector = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.icons.FILTER_LIST, size=18, color=ft.colors.GREY_600),
                type_dropdown_text,
                ft.Icon(ft.icons.ARROW_DROP_DOWN, size=18, color=ft.colors.GREY_600),
            ],
            spacing=4,
        ),
        on_click=_show_type_picker,
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        bgcolor=ft.colors.WHITE,
        ink=True,
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
    apply_no_bounce(scroll_content)

    body = ft.Column(
        controls=[tabs, type_selector, scroll_content],
        spacing=0,
        expand=True,
    )

    view = ft.View(
        route="/ticket/list",
        appbar=ft.AppBar(
            title=ft.Text("作业票"),
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE,
            actions=[
                ft.IconButton(
                    ft.icons.ADD,
                    icon_color=ft.colors.WHITE,
                    on_click=_on_add,
                ),
            ],
        ),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    # 首次加载
    await _init_types()
    await _load(reset=True)

    return view
