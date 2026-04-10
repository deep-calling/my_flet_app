"""视频监控 — 视频播放详情页"""

from __future__ import annotations

import flet as ft


async def build_camera_detail_view(page: ft.Page, camera_id: str) -> ft.View:
    """视频播放页 — TODO: Flet 暂无原生视频播放组件，后续接入"""

    body = ft.Column(
        controls=[
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.icons.VIDEOCAM_OFF, size=64, color=ft.colors.GREY_400),
                        ft.Text(
                            "视频播放功能待实现",
                            size=16,
                            color=ft.colors.GREY_600,
                        ),
                        ft.Text(
                            "TODO: Flet 暂不支持原生视频流播放，需通过 WebView 或外部播放器实现",
                            size=13,
                            color=ft.colors.GREY_400,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                ),
                alignment=ft.alignment.center,
                expand=True,
                padding=ft.padding.only(top=120),
            ),
        ],
        expand=True,
    )

    return ft.View(
        route="/camera/detail",
        appbar=ft.AppBar(title=ft.Text("视频详情"), bgcolor=ft.colors.WHITE),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )
