"""考试详情/解析页 — details.vue + info.vue"""

from __future__ import annotations

import flet as ft

from components.scroll_helper import apply_no_bounce

from services import train_service as ts
from components.detail_page import detail_section
from components.form_fields import readonly_field


# ============================================================
# 考试详情页（含成绩、考试信息）
# ============================================================

async def build_exam_details_view(
    page: ft.Page, exam_id: str, exam_type: str = "2", result_id: str = ""
) -> ft.View:
    """考试详情页：显示考试信息和成绩，可跳转试卷解析"""

    data = [{}]
    try:
        data[0] = await ts.get_exam_details(
            exam_id, result_id=result_id if exam_type == "1" else ""
        ) or {}
    except Exception:
        pass

    d = data[0]
    exam_info = d.get("exam", {})
    score = d.get("score", 0)
    passing_score = d.get("passingScore", 0)
    jggbfs = str(exam_info.get("jggbfs", "2"))

    # 成绩展示区
    if jggbfs == "1":
        score_widget = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.icons.CHECK_CIRCLE, size=48, color=ft.colors.GREEN),
                    ft.Text("已完成考试", size=16, color=ft.colors.GREEN),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=20,
            bgcolor=ft.colors.WHITE,
            alignment=ft.alignment.center,
            margin=ft.margin.only(bottom=10),
        )
    else:
        is_pass = score >= passing_score
        score_color = ft.colors.GREEN if is_pass else ft.colors.RED
        score_widget = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(str(score), size=48, weight=ft.FontWeight.BOLD, color=score_color),
                    ft.Text(
                        "顺利通过" if is_pass else "还需继续努力",
                        size=16, color=score_color,
                    ),
                    ft.Text(f"及格分：{passing_score}", size=13, color=ft.colors.GREY_500),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            padding=20,
            bgcolor=ft.colors.WHITE,
            alignment=ft.alignment.center,
            margin=ft.margin.only(bottom=10),
        )

    # 考试信息
    info_section = detail_section("考试信息", [
        readonly_field("考试名称", exam_info.get("ksmc", "")),
        readonly_field("制定部门", exam_info.get("zdbm", "")),
        readonly_field("制定人", exam_info.get("zdr", "")),
        readonly_field("开始时间", exam_info.get("beginTime", "")),
        readonly_field("结束时间", exam_info.get("endTime", "")),
    ])

    # 操作按钮
    actions_controls: list[ft.Control] = []
    if jggbfs == "3":
        # 公布答案和结果 → 可查看试卷
        async def _view_paper(e):
            if exam_type == "1":
                # 刷题
                await page.go_async(f"/train/info?resultId={result_id}")
            else:
                await page.go_async(f"/train/info?examId={exam_id}&resultId={result_id}")

        actions_controls.append(
            ft.ElevatedButton(
                text="查看试卷",
                on_click=_view_paper,
                bgcolor=ft.colors.BLUE,
                color=ft.colors.WHITE,
                expand=True,
            )
        )

    content_controls = [score_widget, info_section]

    content = ft.Column(controls=content_controls, spacing=0)

    body = ft.Column(
        controls=[
            ft.ListView(controls=[content], expand=True, padding=0),
        ],
        spacing=0,
        expand=True,
    )

    if actions_controls:
        body.controls.append(
            ft.Container(
                content=ft.Row(controls=actions_controls, spacing=12),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                bgcolor=ft.colors.WHITE,
                border=ft.border.only(top=ft.border.BorderSide(1, ft.colors.GREY_200)),
            )
        )

    return ft.View(
        route="/train/details",
        appbar=ft.AppBar(title=ft.Text("考试详情"), bgcolor=ft.colors.WHITE),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )


# ============================================================
# 试卷解析页（info.vue）
# ============================================================

_TYPE_MAP = {"1": "是非题", "2": "单选题", "3": "多选题"}


async def build_exam_info_view(
    page: ft.Page, exam_id: str = "", result_id: str = ""
) -> ft.View:
    """试卷解析页：展示每题的答案和解析"""

    current_page_no = [1]
    page_size = 10
    items_data: list[dict] = []
    is_loading = [False]

    list_column = ft.Column(spacing=0, expand=True)
    loading_ring = ft.ProgressRing(width=24, height=24, visible=False)
    load_more_btn = ft.Container(visible=False)

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
            if result_id:
                params["resultId"] = result_id
            if exam_id:
                params["examId"] = exam_id

            # 根据有无 examId 判断是刷题还是考试
            if result_id and not exam_id:
                result = await ts.get_brush_item_details(params)
            else:
                result = await ts.get_exam_item_details(params)

            records = result.get("records", []) if isinstance(result, dict) else []
            total = result.get("total", 0) if isinstance(result, dict) else 0

            for idx, item in enumerate(records):
                items_data.append(item)
                num = len(items_data)
                list_column.controls.append(_build_question(item, num))

            has_more = len(items_data) < total
            load_more_btn.visible = has_more
            if has_more:
                load_more_btn.content = ft.TextButton(
                    "加载更多", on_click=_on_load_more,
                    style=ft.ButtonStyle(color=ft.colors.BLUE),
                )
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"加载失败：{ex}"), open=True)

        is_loading[0] = False
        loading_ring.visible = False
        await page.update_async()

    async def _on_load_more(e):
        current_page_no[0] += 1
        await _load_data(reset=False)

    def _build_question(item: dict, num: int) -> ft.Control:
        q_type = str(item.get("type", ""))
        type_text = _TYPE_MAP.get(q_type, "")
        is_correct = str(item.get("result", "")) == "1"
        options = item.get("options", [])
        correct = item.get("correct", "")
        answer = item.get("answer", "")
        analysis = item.get("analysis", "")

        # 选项列表
        option_controls: list[ft.Control] = []
        for opt in options:
            xx = opt.get("xx", "")
            xxnr = opt.get("xxnr", "")
            is_correct_opt = xx in correct.split(",")
            is_user_ans = xx in answer.split(",")

            color = ft.colors.BLACK87
            if is_user_ans and not is_correct_opt:
                color = ft.colors.RED
            elif is_correct_opt:
                color = ft.colors.GREEN

            option_controls.append(
                ft.Text(f"{xx}. {xxnr}", size=14, color=color)
            )

        result_icon = ft.Icon(
            ft.icons.CHECK_CIRCLE if is_correct else ft.icons.CANCEL,
            color=ft.colors.GREEN if is_correct else ft.colors.RED,
            size=20,
        )

        controls = [
            ft.Row(controls=[
                ft.Text(f"{num}. [{type_text}]", size=14, weight=ft.FontWeight.W_500, expand=True),
                result_icon,
            ]),
            ft.Text(item.get("content", ""), size=14),
            *option_controls,
            ft.Text(f"正确答案：{correct}", size=13, color=ft.colors.GREEN),
            ft.Text(f"你的答案：{answer}", size=13, color=ft.colors.RED if not is_correct else ft.colors.GREEN),
        ]

        # 解析（仅错题显示）
        if not is_correct and analysis:
            controls.append(
                ft.Container(
                    content=ft.Text(f"解析：{analysis}", size=13, color=ft.colors.ORANGE_700),
                    padding=ft.padding.only(top=4),
                )
            )

        return ft.Container(
            content=ft.Column(controls=controls, spacing=6),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
            margin=ft.margin.only(bottom=8),
            border_radius=8,
        )

    scroll_content = ft.ListView(
        controls=[
            list_column,
            ft.Container(
                content=ft.Row([loading_ring], alignment=ft.MainAxisAlignment.CENTER),
                padding=10,
            ),
            load_more_btn,
        ],
        expand=True,
        padding=ft.padding.all(8),
    )
    apply_no_bounce(scroll_content)

    view = ft.View(
        route="/train/info",
        appbar=ft.AppBar(title=ft.Text("试卷解析"), bgcolor=ft.colors.WHITE),
        controls=[scroll_content],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    await _load_data(reset=True)
    return view
