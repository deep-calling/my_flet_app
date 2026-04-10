"""通用详情页模板 — AppBar + 滚动内容 + 底部操作按钮"""

from __future__ import annotations

import asyncio
from typing import Callable, Awaitable

import flet as ft


async def build_detail_page(
    page: ft.Page,
    *,
    title: str,
    record_id: str,
    on_load_data: Callable[[str], Awaitable[dict]],
    build_content: Callable[[dict], ft.Control],
    actions: list[dict] | None = None,
) -> ft.View:
    """构建通用详情页 View。

    先返回带 loading 的 View，数据异步加载后再渲染内容，避免阻塞 UI。

    参数:
        record_id: 记录 ID
        on_load_data: async (id) -> dict，加载详情数据
        build_content: (data_dict) -> Control，渲染页面内容
        actions: [{label, on_click: async(e), style: 'primary'|'danger'|'default'}]
    """
    actions = actions or []

    # 加载中占位
    loading = ft.Container(
        content=ft.ProgressRing(width=32, height=32),
        alignment=ft.alignment.center,
        expand=True,
    )

    # 错误占位
    error_widget = ft.Container(visible=False, expand=True)

    # 内容区
    content_area = ft.Container(expand=True)

    # --- 底部操作按钮栏 ---
    bottom_bar = ft.Container(visible=False)
    if actions:
        btn_controls: list[ft.Control] = []
        for act in actions:
            style = act.get("style", "default")
            if style == "primary":
                btn = ft.ElevatedButton(
                    text=act["label"],
                    on_click=act["on_click"],
                    bgcolor=ft.colors.BLUE,
                    color=ft.colors.WHITE,
                    expand=True,
                )
            elif style == "danger":
                btn = ft.ElevatedButton(
                    text=act["label"],
                    on_click=act["on_click"],
                    bgcolor=ft.colors.RED,
                    color=ft.colors.WHITE,
                    expand=True,
                )
            else:
                btn = ft.OutlinedButton(
                    text=act["label"],
                    on_click=act["on_click"],
                    expand=True,
                )
            btn_controls.append(btn)

        bottom_bar = ft.Container(
            content=ft.Row(controls=btn_controls, spacing=12),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            bgcolor=ft.colors.WHITE,
            border=ft.border.only(top=ft.border.BorderSide(1, ft.colors.GREY_200)),
            visible=True,
        )

    body = ft.Column(
        controls=[loading, error_widget, content_area, bottom_bar],
        spacing=0,
        expand=True,
    )

    view = ft.View(
        route=f"/{title}",
        appbar=ft.AppBar(title=ft.Text(title), bgcolor=ft.colors.WHITE),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    # --- 异步加载数据（View 显示后再执行） ---
    async def _load_async():
        try:
            data = await on_load_data(record_id)
            content_ctrl = build_content(data)
            content_area.content = ft.ListView(
                controls=[content_ctrl] if not isinstance(content_ctrl, list) else content_ctrl,
                expand=True,
                padding=0,
            )
            loading.visible = False
        except Exception as ex:
            loading.visible = False
            error_widget.visible = True
            error_widget.content = ft.Column(
                controls=[
                    ft.Icon(ft.icons.ERROR_OUTLINE, size=48, color=ft.colors.RED_300),
                    ft.Text(f"加载失败：{ex}", size=14, color=ft.colors.GREY_600),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
            )
            error_widget.alignment = ft.alignment.center
        await page.update_async()

    asyncio.ensure_future(_load_async())

    return view


def detail_section(title: str, fields: list[ft.Control]) -> ft.Container:
    """详情页内的分组卡片：标题 + 字段列表。

    常与 form_fields.readonly_field 配合使用。
    """
    return ft.Container(
        bgcolor=ft.colors.WHITE,
        margin=ft.margin.only(bottom=10),
        padding=ft.padding.only(bottom=4),
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Text(title, size=15, weight=ft.FontWeight.W_500),
                    padding=ft.padding.symmetric(horizontal=16, vertical=10),
                    border=ft.border.only(
                        bottom=ft.border.BorderSide(1, ft.colors.GREY_200)
                    ),
                ),
                *fields,
            ],
            spacing=0,
        ),
    )
