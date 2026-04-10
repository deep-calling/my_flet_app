"""首页 — 业务模块菜单入口"""

import asyncio

import flet as ft

from services.api_client import api_client
from utils.app_state import app_state

# 菜单数据：title + menus(name, icon, route)
MENU_DATA = [
    {
        "title": "双重预防",
        "menus": [
            {"name": "风险分析对象", "icon": ft.icons.WARNING_AMBER_ROUNDED, "route": "/trouble/risk_analysis_object"},
            {"name": "风险分析单元", "icon": ft.icons.WARNING_AMBER_ROUNDED, "route": "/trouble/risk_analysis_unit"},
            {"name": "风险分析事件", "icon": ft.icons.WARNING_AMBER_ROUNDED, "route": "/trouble/risk_analysis_event"},
            {"name": "风险管控措施", "icon": ft.icons.WARNING_AMBER_ROUNDED, "route": "/trouble/risk_manage_measure"},
            {"name": "隐患任务", "icon": ft.icons.ASSIGNMENT, "route": "/trouble/tasks"},
            {"name": "隐患排查记录", "icon": ft.icons.FACT_CHECK, "route": "/trouble/record"},
            {"name": "隐患整改", "icon": ft.icons.BUILD_CIRCLE, "route": "/trouble/rectificat"},
            {"name": "隐患上报", "icon": ft.icons.REPORT, "route": "/trouble/handle"},
            {"name": "包保责任制任务", "icon": ft.icons.ASSIGNMENT, "route": "/troublebbzrz/tasks"},
            {"name": "包保排查记录", "icon": ft.icons.FACT_CHECK, "route": "/troublebbzrz/record"},
            {"name": "包保责任制整改", "icon": ft.icons.BUILD_CIRCLE, "route": "/troublebbzrz/rectificat"},
            {"name": "包保责任制上报", "icon": ft.icons.REPORT, "route": "/troublebbzrz/handle"},
        ],
    },
    {
        "title": "安全风险分区分级",
        "menus": [
            {"name": "风险研判", "icon": ft.icons.ANALYTICS, "route": "/security/read"},
            {"name": "应急卡", "icon": ft.icons.EMERGENCY, "route": "/security/emergency"},
            {"name": "应知卡", "icon": ft.icons.INFO, "route": "/security/know"},
            {"name": "承诺卡", "icon": ft.icons.HANDSHAKE, "route": "/security/commitment"},
            {"name": "管控清单", "icon": ft.icons.CHECKLIST, "route": "/security/controls"},
            {"name": "辨识清单", "icon": ft.icons.SEARCH, "route": "/security/identify"},
            {"name": "风险点台账", "icon": ft.icons.LOCATION_ON, "route": "/security/risk_point"},
            {"name": "风险分区台账", "icon": ft.icons.MAP, "route": "/security/risk_area"},
        ],
    },
    {
        "title": "电子巡检",
        "menus": [
            {"name": "巡检任务", "icon": ft.icons.CHECKLIST_RTL, "route": "/inspection/tasks"},
        ],
    },
    {
        "title": "作业票",
        "menus": [
            {"name": "作业申请", "icon": ft.icons.ASSIGNMENT, "route": "/ticket/apply"},
            {"name": "作业票", "icon": ft.icons.RECEIPT_LONG, "route": "/ticket/list"},
        ],
    },
    {
        "title": "培训考试管理",
        "menus": [
            {"name": "线下培训", "icon": ft.icons.SCHOOL, "route": "/train/offline"},
            {"name": "线上培训", "icon": ft.icons.LAPTOP, "route": "/train/online"},
            {"name": "学习资料", "icon": ft.icons.MENU_BOOK, "route": "/train/materials"},
            {"name": "在线刷题", "icon": ft.icons.QUIZ, "route": "/train/brush"},
            {"name": "在线考试", "icon": ft.icons.EDIT_NOTE, "route": "/train/test"},
        ],
    },
    {
        "title": "应急演练",
        "menus": [
            {"name": "演练计划", "icon": ft.icons.EVENT_NOTE, "route": "/emergency/plan"},
            {"name": "应急队伍", "icon": ft.icons.GROUPS, "route": "/emergency/team"},
            {"name": "应急物资", "icon": ft.icons.INVENTORY, "route": "/emergency/material"},
        ],
    },
    {
        "title": "二道门记录",
        "menus": [
            {"name": "人员进出", "icon": ft.icons.PERSON_PIN, "route": "/record/people"},
            {"name": "车辆进出", "icon": ft.icons.DIRECTIONS_CAR, "route": "/record/car"},
        ],
    },
    {
        "title": "视频监控",
        "menus": [
            {"name": "视频监控", "icon": ft.icons.VIDEOCAM, "route": "/camera"},
        ],
    },
    {
        "title": "报警处理",
        "menus": [
            {"name": "人员定位", "icon": ft.icons.PERSON_PIN_CIRCLE, "route": "/alarm/personnel"},
            {"name": "监测报警", "icon": ft.icons.NOTIFICATION_IMPORTANT, "route": "/alarm/indicators"},
        ],
    },
]


def _build_menu_item(page: ft.Page, name: str, icon: str, route: str, need_action: bool = False):
    """构建单个菜单项：图标 + 名称"""

    async def on_tap(e):
        await page.go_async(route)

    icon_widget = ft.Icon(icon, size=36, color=ft.colors.BLUE_600)
    # 有待办提醒时显示红点
    if need_action:
        icon_widget.badge = ft.Badge(small_size=8)

    return ft.Container(
        width=80,
        content=ft.Column(
            controls=[
                icon_widget,
                ft.Text(name, size=12, color=ft.colors.GREY_700, text_align=ft.TextAlign.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        ),
        padding=ft.padding.symmetric(vertical=8),
        on_click=on_tap,
        ink=True,
    )


def _build_menu_section(page: ft.Page, title: str, menus: list, remind_names: set | None = None):
    """构建一个菜单分组：标题 + 网格"""
    remind_names = remind_names or set()

    # 标题行：蓝色竖条 + 标题文字
    title_row = ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(width=4, height=16, bgcolor=ft.colors.BLUE, border_radius=2),
                ft.Text(title, size=14, weight=ft.FontWeight.W_500),
            ],
            spacing=8,
        ),
        border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_300)),
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
    )

    # 菜单网格：每行 4 个
    items = []
    for m in menus:
        need_action = m["name"] in remind_names
        items.append(_build_menu_item(page, m["name"], m["icon"], m["route"], need_action))

    rows = []
    for i in range(0, len(items), 4):
        row_items = items[i : i + 4]
        # 补齐空位保持对齐
        while len(row_items) < 4:
            row_items.append(ft.Container(width=80))
        rows.append(ft.Row(controls=row_items, alignment=ft.MainAxisAlignment.SPACE_AROUND))

    return ft.Container(
        bgcolor=ft.colors.WHITE,
        margin=ft.margin.only(top=10),
        border_radius=0,
        content=ft.Column(
            controls=[title_row, *rows],
            spacing=0,
        ),
        padding=ft.padding.only(bottom=10),
    )


async def build_home_content(page: ft.Page) -> ft.Control:
    """构建首页内容（不含 NavigationBar，由主框架包裹）。
    先立即渲染静态菜单，再后台异步加载红点提醒和轮播图。"""

    # --- 顶部导航栏 ---
    async def go_message(e):
        await page.go_async("/message")

    msg_icon_container = ft.Container(
        content=ft.Icon(ft.icons.MAIL_OUTLINE, color=ft.colors.GREY_800, size=24),
        on_click=go_message,
    )

    top_bar = ft.Container(
        bgcolor=ft.colors.WHITE,
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
        content=ft.Row(
            controls=[
                msg_icon_container,
                ft.Text(
                    "安全生产信息化管理平台",
                    size=18,
                    weight=ft.FontWeight.W_500,
                    text_align=ft.TextAlign.CENTER,
                    expand=True,
                ),
                ft.Container(width=24),  # 右侧占位，保持标题居中
            ],
        ),
    )

    # --- 轮播图占位 ---
    banner_container = ft.Container(
        bgcolor=ft.colors.WHITE,
        padding=ft.padding.only(left=16, right=16, bottom=16),
        content=ft.Container(
            height=140,
            bgcolor=ft.colors.BLUE_50,
            border_radius=8,
            alignment=ft.alignment.center,
            content=ft.Text("轮播图", color=ft.colors.BLUE_200, size=16),
        ),
    )

    # --- 菜单分组（静态，无红点，立即渲染） ---
    menu_sections = []
    for group in MENU_DATA:
        menu_sections.append(
            _build_menu_section(page, group["title"], group["menus"])
        )

    list_view = ft.ListView(
        controls=[banner_container, *menu_sections],
        expand=True,
        padding=0,
    )

    content = ft.Column(
        controls=[top_bar, list_view],
        spacing=0,
        expand=True,
    )

    # --- 后台异步加载动态数据（红点 + 轮播图） ---
    async def _load_dynamic_data():
        async def _fetch_msg():
            try:
                return await api_client.get(
                    "/jeecg-boot/sys/sysAnnouncementSend/getMyAnnouncementSend",
                    params={"pageNo": 1, "pageSize": 1, "readFlag": 0},
                )
            except Exception:
                return None

        async def _fetch_epi():
            try:
                return await api_client.get("/jeecg-boot/app/epi/recordRemind")
            except Exception:
                return None

        async def _fetch_rect():
            try:
                return await api_client.get("/jeecg-boot/app/dangerRect/dangerRectRemind")
            except Exception:
                return None

        async def _fetch_record():
            try:
                return await api_client.get("/jeecg-boot/app/dangerRect/dangerRecordRemind")
            except Exception:
                return None

        async def _fetch_slides():
            try:
                return await api_client.get("/jeecg-boot/app/system/slideshow")
            except Exception:
                return None

        msg_result, epi_result, rect_result, record_result, slides_result = await asyncio.gather(
            _fetch_msg(), _fetch_epi(), _fetch_rect(), _fetch_record(), _fetch_slides()
        )

        # 更新消息红点
        if msg_result and msg_result.get("total", 0) > 0:
            msg_icon = ft.Icon(ft.icons.MAIL_OUTLINE, color=ft.colors.GREY_800, size=24)
            msg_icon.badge = ft.Badge(small_size=8)
            msg_icon_container.content = msg_icon

        # 收集需要红点的菜单名
        remind_names: set[str] = set()
        if epi_result and int(epi_result) > 0:
            remind_names.add("巡检任务")
        if rect_result:
            if int(rect_result.get("0", 0)) > 0:
                remind_names.add("隐患整改")
            if int(rect_result.get("1", 0)) > 0:
                remind_names.add("包保责任制整改")
        if record_result:
            if int(record_result.get("0", 0)) > 0:
                remind_names.add("隐患排查记录")
            if int(record_result.get("1", 0)) > 0:
                remind_names.add("包保排查记录")

        # 有红点提醒时重建菜单分组
        if remind_names:
            new_sections = []
            for group in MENU_DATA:
                new_sections.append(
                    _build_menu_section(page, group["title"], group["menus"], remind_names)
                )
            list_view.controls = [banner_container, *new_sections]

        # 更新轮播图
        if slides_result and len(slides_result) > 0:
            img_url = f"{app_state.host}/jeecg-boot/sys/common/static/{slides_result[0]}"
            banner_container.content = ft.Container(
                height=140,
                border_radius=8,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                content=ft.Image(src=img_url, fit=ft.ImageFit.COVER, expand=True),
            )

        try:
            await page.update_async()
        except Exception:
            pass  # 页面可能已切走

    asyncio.create_task(_load_dynamic_data())

    return content
