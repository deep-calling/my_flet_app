"""考试结果页"""

from __future__ import annotations

import flet as ft

from services import train_service as ts


async def build_results_view(
    page: ft.Page, exam_id: str, exam_type: str = "2", result_id: str = ""
) -> ft.View:
    """考试结果页：显示分数和通过情况

    exam_type: '1'=刷题, '2'=考试
    """

    score_text = ft.Text("", size=48, weight=ft.FontWeight.BOLD)
    result_text = ft.Text("", size=16)
    result_icon = ft.Icon(ft.icons.CHECK_CIRCLE, size=64, color=ft.colors.GREEN)

    try:
        data = await ts.get_exam_details(exam_id, result_id=result_id if exam_type == "1" else "")
        if isinstance(data, dict):
            score = data.get("score", 0)
            passing_score = data.get("passingScore", 0)
            exam_info = data.get("exam", {})
            jggbfs = str(exam_info.get("jggbfs", "2"))

            if jggbfs == "1":
                # 不公布成绩
                result_icon.name = ft.icons.CHECK_CIRCLE
                result_icon.color = ft.colors.GREEN
                result_text.value = "恭喜您，完成考试!"
                score_text.visible = False
            else:
                # 公布成绩
                score_text.value = str(score)
                score_text.visible = True
                if score >= passing_score:
                    score_text.color = ft.colors.GREEN
                    result_icon.name = ft.icons.CHECK_CIRCLE
                    result_icon.color = ft.colors.GREEN
                    result_text.value = "顺利通过"
                else:
                    score_text.color = ft.colors.RED
                    result_icon.name = ft.icons.CANCEL
                    result_icon.color = ft.colors.RED
                    result_text.value = "还需继续努力"
    except Exception as ex:
        result_text.value = f"加载失败：{ex}"

    async def _on_back(e):
        # 跳过考试页，返回列表
        if len(page.views) > 2:
            page.views.pop()
            page.views.pop()
        elif page.views:
            page.views.pop()
        await page.update_async()

    content = ft.Column(
        controls=[
            ft.Container(height=40),
            result_icon,
            ft.Container(height=16),
            score_text,
            ft.Container(height=8),
            result_text,
            ft.Container(height=40),
            ft.ElevatedButton(
                text="返回",
                on_click=_on_back,
                bgcolor=ft.colors.BLUE,
                color=ft.colors.WHITE,
                width=200,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.START,
        expand=True,
    )

    return ft.View(
        route="/train/results",
        appbar=ft.AppBar(
            title=ft.Text("考试结果"),
            bgcolor=ft.colors.WHITE,
            automatically_imply_leading=False,
        ),
        controls=[content],
        padding=0,
        bgcolor=ft.colors.WHITE,
    )
