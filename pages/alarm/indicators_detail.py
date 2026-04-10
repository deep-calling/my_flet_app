"""监测报警 — 处理详情页"""

from __future__ import annotations

import flet as ft

from services import alarm_service as als


async def build_indicators_detail_view(page: ft.Page, alarm_id: str) -> ft.View:
    """监测报警处理表单"""

    # 状态选项：是否筛选
    screening_options = [
        {"value": "0", "label": "否"},
        {"value": "1", "label": "是"},
    ]

    have_screening = [""]
    deal_result_ref = ft.Ref[ft.TextField]()

    async def _submit(e):
        if not have_screening[0]:
            page.snack_bar = ft.SnackBar(ft.Text("请选择处理状态"), open=True)
            await page.update_async()
            return
        if not deal_result_ref.current.value:
            page.snack_bar = ft.SnackBar(ft.Text("请输入处理结果"), open=True)
            await page.update_async()
            return

        try:
            await als.deal_sensor_alarm({
                "alarmId": alarm_id,
                "haveScreening": have_screening[0],
                "dealResult": deal_result_ref.current.value,
            })
            page.snack_bar = ft.SnackBar(ft.Text("操作成功"), open=True)
            await page.update_async()
            page.views.pop()
            await page.update_async()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"提交失败：{ex}"), open=True)
            await page.update_async()

    async def _on_screening_change(e):
        have_screening[0] = e.control.value

    form = ft.Column(
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Dropdown(
                        label="处理状态",
                        options=[ft.dropdown.Option(key=o["value"], text=o["label"]) for o in screening_options],
                        on_change=_on_screening_change,
                        border_color=ft.colors.GREY_300,
                    ),
                    ft.TextField(
                        ref=deal_result_ref,
                        label="处理结果",
                        multiline=True,
                        min_lines=3,
                        max_lines=6,
                        max_length=300,
                        border_color=ft.colors.GREY_300,
                    ),
                    ft.ElevatedButton(
                        text="提交",
                        on_click=_submit,
                        bgcolor=ft.colors.BLUE,
                        color=ft.colors.WHITE,
                        width=float("inf"),
                    ),
                ], spacing=16),
                padding=ft.padding.all(16),
            ),
        ],
        spacing=0,
        expand=True,
    )

    return ft.View(
        route="/alarm/indicators_detail",
        appbar=ft.AppBar(title=ft.Text("报警详情"), bgcolor=ft.colors.WHITE),
        controls=[form],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )
