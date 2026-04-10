"""修改密码 — 表单页"""

from __future__ import annotations

import re

import flet as ft

from services.auth_service import update_password
from utils.app_state import app_state


async def build_change_password_view(page: ft.Page) -> ft.View:
    """修改密码表单"""

    old_pwd = ft.Ref[ft.TextField]()
    new_pwd = ft.Ref[ft.TextField]()
    confirm_pwd = ft.Ref[ft.TextField]()

    pwd_pattern = re.compile(r"(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[~!@#$%^&*_.]).{8,}")

    async def _submit(e):
        old_val = old_pwd.current.value or ""
        new_val = new_pwd.current.value or ""
        confirm_val = confirm_pwd.current.value or ""

        if not old_val:
            page.snack_bar = ft.SnackBar(ft.Text("原密码不能为空"), open=True)
            await page.update_async()
            return
        if not new_val:
            page.snack_bar = ft.SnackBar(ft.Text("修改密码不能为空"), open=True)
            await page.update_async()
            return
        if not pwd_pattern.match(new_val):
            page.snack_bar = ft.SnackBar(
                ft.Text("密码由8位数字、大小写字母和特殊字符组成"), open=True
            )
            await page.update_async()
            return
        if new_val != confirm_val:
            page.snack_bar = ft.SnackBar(ft.Text("修改密码和确认密码不一致"), open=True)
            await page.update_async()
            return

        try:
            await update_password(old_val, new_val, confirm_val)
            page.snack_bar = ft.SnackBar(ft.Text("修改成功"), open=True)
            await page.update_async()
            page.views.pop()
            await page.update_async()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"修改失败：{ex}"), open=True)
            await page.update_async()

    form = ft.Container(
        bgcolor=ft.colors.WHITE,
        padding=ft.padding.all(16),
        content=ft.Column(
            controls=[
                ft.TextField(
                    ref=old_pwd,
                    label="原密码",
                    password=True,
                    can_reveal_password=True,
                    border_color=ft.colors.GREY_300,
                ),
                ft.TextField(
                    ref=new_pwd,
                    label="修改密码",
                    password=True,
                    can_reveal_password=True,
                    border_color=ft.colors.GREY_300,
                ),
                ft.TextField(
                    ref=confirm_pwd,
                    label="确认密码",
                    password=True,
                    can_reveal_password=True,
                    border_color=ft.colors.GREY_300,
                ),
                ft.Container(height=16),
                ft.ElevatedButton(
                    text="确认",
                    on_click=_submit,
                    bgcolor=ft.colors.BLUE,
                    color=ft.colors.WHITE,
                    width=float("inf"),
                ),
            ],
            spacing=12,
        ),
    )

    return ft.View(
        route="/my/change_password",
        appbar=ft.AppBar(title=ft.Text("修改密码"), bgcolor=ft.colors.WHITE),
        controls=[form],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )
