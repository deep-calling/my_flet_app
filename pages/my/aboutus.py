"""关于我们 — 静态页面"""

from __future__ import annotations

import flet as ft


async def build_aboutus_view(page: ft.Page) -> ft.View:
    """关于我们页面"""

    body = ft.Column(
        controls=[
            ft.Container(
                bgcolor=ft.colors.WHITE,
                margin=ft.margin.only(top=16),
                content=ft.ListTile(
                    title=ft.Text("检查新版本", size=14),
                    trailing=ft.Text("当前版本：1.0.0", size=13, color=ft.colors.GREY_500),
                ),
            ),
            ft.Container(expand=True),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "软件许可及服务协议",
                            size=14,
                            color=ft.colors.BLUE,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.only(bottom=40),
                alignment=ft.alignment.center,
            ),
        ],
        expand=True,
    )

    return ft.View(
        route="/my/aboutus",
        appbar=ft.AppBar(title=ft.Text("关于我们"), bgcolor=ft.colors.WHITE),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )
