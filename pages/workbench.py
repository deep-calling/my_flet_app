"""工作台 — 待办事项 + 报警统计 + 作业票看板"""

import asyncio

import flet as ft

from services.api_client import api_client


def _build_stat_card(label: str, value: str):
    """单个统计卡片"""
    return ft.Container(
        expand=True,
        padding=ft.padding.symmetric(vertical=12),
        alignment=ft.alignment.center,
        content=ft.Column(
            controls=[
                ft.Text(value, size=28, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Text(label, size=12, color=ft.colors.GREY_600, text_align=ft.TextAlign.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        ),
    )


def _build_section(title: str, cards: list[ft.Control]):
    """一个统计分区：标题 + 3 列卡片"""
    return ft.Container(
        bgcolor=ft.colors.WHITE,
        margin=ft.margin.only(left=16, right=16, top=12),
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        content=ft.Column(
            controls=[
                ft.Container(
                    padding=ft.padding.only(left=8, top=8, bottom=4),
                    content=ft.Text(title, size=15, weight=ft.FontWeight.W_500),
                ),
                ft.Row(controls=cards, alignment=ft.MainAxisAlignment.SPACE_AROUND),
            ],
            spacing=0,
        ),
    )


async def build_workbench_content(page: ft.Page) -> ft.Control:
    """构建工作台内容"""

    # 并发加载所有数据
    async def _fetch_commission():
        try:
            return await api_client.get("/jeecg-boot/app/work/commission")
        except Exception:
            return None

    async def _fetch_alarm():
        try:
            return await api_client.get("/jeecg-boot/app/work/alarmCount")
        except Exception:
            return None

    async def _fetch_ticket():
        try:
            return await api_client.get("/jeecg-boot/home/ticket")
        except Exception:
            return None

    commission_result, alarm_result, ticket_result = await asyncio.gather(
        _fetch_commission(), _fetch_alarm(), _fetch_ticket()
    )

    count_info: dict = commission_result or {}
    gas_alarm: dict = {}
    process_alarm: dict = {}
    if alarm_result:
        gas_alarm = alarm_result.get("gasAlarm", {})
        process_alarm = alarm_result.get("processAlarm", {})

    # 构建作业票图表
    ticket_chart = ft.Container(
        height=240,
        bgcolor=ft.colors.GREY_50,
        border_radius=8,
        alignment=ft.alignment.center,
        content=ft.Text("暂无作业票数据", color=ft.colors.GREY_400),
    )
    try:
        if ticket_result and ticket_result.get("fields"):
            result = ticket_result
            fields = result["fields"]
            source_data = result.get("sourceData", [])
            # 构建柱状图
            bar_groups = []
            colors = [ft.colors.BLUE, ft.colors.ORANGE, ft.colors.GREEN, ft.colors.RED]
            for i, field in enumerate(fields):
                rods = []
                for j, sd in enumerate(source_data):
                    val = float(sd.get(field, 0))
                    rods.append(
                        ft.BarChartRod(
                            from_y=0,
                            to_y=val,
                            width=12,
                            color=colors[j % len(colors)],
                            tooltip=f"{sd['name']}: {val}",
                            border_radius=2,
                        )
                    )
                # 截取票名（去掉"作业票"后缀）
                short_name = field[:-2] if field.endswith("作业票") else field
                bar_groups.append(
                    ft.BarChartGroup(x=i, bar_rods=rods)
                )

            import math

            bottom_labels = []
            for i, field in enumerate(fields):
                short_name = field[:-2] if field.endswith("作业票") else field
                bottom_labels.append(
                    ft.ChartAxisLabel(
                        value=i,
                        label=ft.Container(
                            content=ft.Text(
                                short_name,
                                size=10,
                                no_wrap=True,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            rotate=ft.Rotate(
                                angle=-math.pi / 6,  # -30°
                                alignment=ft.alignment.center,
                            ),
                            padding=ft.padding.only(top=18),
                            alignment=ft.alignment.center,
                        ),
                    )
                )

            ticket_chart = ft.BarChart(
                bar_groups=bar_groups,
                bottom_axis=ft.ChartAxis(labels=bottom_labels, labels_size=60),
                left_axis=ft.ChartAxis(labels_size=40),
                border=ft.border.all(0, ft.colors.TRANSPARENT),
                horizontal_grid_lines=ft.ChartGridLines(
                    color=ft.colors.GREY_200, width=1, dash_pattern=[3, 3]
                ),
                max_y=max(
                    (float(sd.get(f, 0)) for f in fields for sd in source_data),
                    default=10,
                ) * 1.2 or 10,
                interactive=True,
                expand=True,
                height=240,
            )
    except Exception:
        pass

    # --- 顶部标题 ---
    top_bar = ft.Container(
        bgcolor=ft.colors.WHITE,
        padding=ft.padding.symmetric(horizontal=16, vertical=14),
        content=ft.Text("工作台", size=18, weight=ft.FontWeight.W_500),
    )

    # --- 待办事项 ---
    todo_section = _build_section("待办事项", [
        _build_stat_card("隐患整改", str(count_info.get("dangerCount", 0))),
        _build_stat_card("风险研判", str(count_info.get("announcementCount", 0))),
        _build_stat_card("电子巡检", str(count_info.get("epiInspectionCount", 0))),
    ])

    todo_section2 = ft.Container(
        bgcolor=ft.colors.WHITE,
        margin=ft.margin.only(left=16, right=16),
        border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8),
        padding=ft.padding.only(left=8, right=8, bottom=8),
        content=ft.Row(
            controls=[
                _build_stat_card("隐患排查", str(count_info.get("dangerCheckCount", 0))),
                _build_stat_card("在线考试", str(count_info.get("examCount", 0))),
                ft.Container(expand=True),  # 占位
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        ),
    )

    # --- 工艺参数报警 ---
    process_section = _build_section("工艺参数报警", [
        _build_stat_card("今日报警", str(process_alarm.get("alarmCount", 0))),
        _build_stat_card("已处理", str(process_alarm.get("handled", 0))),
        _build_stat_card("待处理", str(process_alarm.get("untreated", 0))),
    ])

    # --- 有毒可燃气体 ---
    gas_section = _build_section("有毒可燃气体", [
        _build_stat_card("今日报警", str(gas_alarm.get("alarmCount", 0))),
        _build_stat_card("已处理", str(gas_alarm.get("handled", 0))),
        _build_stat_card("待处理", str(gas_alarm.get("untreated", 0))),
    ])

    # --- 作业清单看板 ---
    ticket_section = ft.Container(
        bgcolor=ft.colors.WHITE,
        margin=ft.margin.only(left=16, right=16, top=12, bottom=12),
        border_radius=8,
        padding=ft.padding.all(12),
        content=ft.Column(
            controls=[
                ft.Text("作业清单看板", size=15, weight=ft.FontWeight.W_500),
                ticket_chart,
            ],
            spacing=8,
        ),
    )

    return ft.Column(
        controls=[
            top_bar,
            ft.ListView(
                controls=[todo_section, todo_section2, process_section, gas_section, ticket_section],
                expand=True,
                padding=0,
            ),
        ],
        spacing=0,
        expand=True,
    )
