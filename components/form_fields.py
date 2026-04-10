"""表单字段快速构建 — 对应原项目 u-form + u-form-item"""

from __future__ import annotations

from typing import Any, Callable

import flet as ft


def form_item(label: str, control: ft.Control, required: bool = False) -> ft.Container:
    """带标签的表单行布局"""
    label_parts: list[ft.Control] = []
    if required:
        label_parts.append(ft.Text("*", color=ft.colors.RED, size=14))
    label_parts.append(ft.Text(label, size=14, color=ft.colors.GREY_700, width=100))

    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Row(controls=label_parts, spacing=2, tight=True),
                ft.Container(content=control, expand=True),
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
        bgcolor=ft.colors.WHITE,
    )


def text_field(
    label: str,
    value: str = "",
    on_change: Callable | None = None,
    required: bool = False,
    hint: str = "请输入",
    **kwargs: Any,
) -> ft.Container:
    """带标签的输入框"""
    tf = ft.TextField(
        value=value,
        hint_text=hint,
        on_change=on_change,
        border_color=ft.colors.GREY_300,
        focused_border_color=ft.colors.BLUE,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
        text_size=14,
        **kwargs,
    )
    return form_item(label, tf, required=required)


def dropdown_field(
    label: str,
    value: str = "",
    options: list[dict] | None = None,
    on_change: Callable | None = None,
    required: bool = False,
    hint: str = "请选择",
) -> ft.Container:
    """带标签的下拉选择。options 格式：[{text, value}]"""
    options = options or []
    dd = ft.Dropdown(
        value=value or None,
        hint_text=hint,
        on_change=on_change,
        border_color=ft.colors.GREY_300,
        focused_border_color=ft.colors.BLUE,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
        text_size=14,
        options=[ft.dropdown.Option(key=o["value"], text=o["text"]) for o in options],
    )
    return form_item(label, dd, required=required)


def radio_field(
    label: str,
    value: str = "",
    options: list[dict] | None = None,
    on_change: Callable | None = None,
    required: bool = False,
) -> ft.Container:
    """带标签的单选组。options 格式：[{text, value}]"""
    options = options or []
    rg = ft.RadioGroup(
        value=value or None,
        on_change=on_change,
        content=ft.Row(
            controls=[
                ft.Radio(value=o["value"], label=o["text"]) for o in options
            ],
            wrap=True,
        ),
    )
    return form_item(label, rg, required=required)


def date_field(
    label: str,
    value: str = "",
    on_change: Callable | None = None,
    required: bool = False,
    hint: str = "请选择日期",
) -> ft.Container:
    """带标签的日期选择（点击文本弹出 DatePicker）。

    注意：DatePicker 需要挂到 page.overlay，实际使用时由调用方负责。
    此处返回一个可点击的显示区域 + 隐藏的 TextField 存值。
    """
    tf = ft.TextField(
        value=value,
        hint_text=hint,
        read_only=True,
        on_click=on_change,  # 调用方在 on_click 里打开 DatePicker
        border_color=ft.colors.GREY_300,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
        text_size=14,
        suffix_icon=ft.icons.CALENDAR_TODAY,
    )
    return form_item(label, tf, required=required)


def textarea_field(
    label: str,
    value: str = "",
    on_change: Callable | None = None,
    required: bool = False,
    hint: str = "请输入",
    rows: int = 3,
) -> ft.Container:
    """带标签的多行输入框"""
    tf = ft.TextField(
        value=value,
        hint_text=hint,
        on_change=on_change,
        multiline=True,
        min_lines=rows,
        max_lines=rows + 2,
        border_color=ft.colors.GREY_300,
        focused_border_color=ft.colors.BLUE,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
        text_size=14,
    )
    return form_item(label, tf, required=required)


def readonly_field(label: str, value: str = "") -> ft.Container:
    """只读展示字段：标签 + 值"""
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(label, size=14, color=ft.colors.GREY_700, width=100),
                ft.Text(value or "-", size=14, color=ft.colors.BLACK87, expand=True),
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        bgcolor=ft.colors.WHITE,
    )
