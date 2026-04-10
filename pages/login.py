"""登录页 — 五位一体安全生产信息化管理平台"""

import json

import flet as ft

from config import app_config
from services.auth_service import login
from utils.app_state import app_state


async def build_login_view(page: ft.Page) -> ft.View:
    """构建登录页视图"""

    # 从 client_storage 读取记住的账号密码
    saved_username = await page.client_storage.get_async("username") or ""
    saved_password = await page.client_storage.get_async("password") or ""
    saved_flag = await page.client_storage.get_async("remember_flag") or "1"
    remember = saved_flag == "1"

    # --- 控件 ---
    username_field = ft.TextField(
        label="账号",
        hint_text="请输入账号",
        prefix_icon=ft.icons.PERSON,
        value=saved_username,
        border_color=ft.colors.WHITE54,
        color=ft.colors.WHITE,
        label_style=ft.TextStyle(color=ft.colors.WHITE70),
        cursor_color=ft.colors.WHITE,
    )

    password_field = ft.TextField(
        label="密码",
        hint_text="请输入密码",
        prefix_icon=ft.icons.LOCK,
        value=saved_password,
        password=True,
        can_reveal_password=True,
        border_color=ft.colors.WHITE54,
        color=ft.colors.WHITE,
        label_style=ft.TextStyle(color=ft.colors.WHITE70),
        cursor_color=ft.colors.WHITE,
    )

    remember_cb = ft.Checkbox(
        label="记住密码",
        value=remember,
        check_color=ft.colors.WHITE,
        label_style=ft.TextStyle(color=ft.colors.WHITE),
    )

    # 记住密码切换
    async def on_remember_change(e):
        if not remember_cb.value:
            await page.client_storage.remove_async("username")
            await page.client_storage.remove_async("password")
            await page.client_storage.set_async("remember_flag", "0")
        else:
            await page.client_storage.set_async("username", username_field.value)
            await page.client_storage.set_async("password", password_field.value)
            await page.client_storage.set_async("remember_flag", "1")

    remember_cb.on_change = on_remember_change

    # 跳转登录配置
    async def go_login_set(e):
        await page.go_async("/login_set")

    login_set_btn = ft.TextButton(
        text="登录配置",
        style=ft.ButtonStyle(color=ft.colors.WHITE),
        on_click=go_login_set,
    )

    # 登录逻辑
    login_button = ft.ElevatedButton(
        text="登录",
        width=280,
        color=ft.colors.WHITE,
        bgcolor=ft.colors.BLUE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=25)),
    )

    async def on_login(e):
        # 校验 host
        if not app_config.host:
            page.snack_bar = ft.SnackBar(ft.Text("请先进行登录配置（设置IP和端口）"), open=True)
            await page.update_async()
            return

        username = username_field.value.strip()
        password = password_field.value.strip()

        if not username:
            page.snack_bar = ft.SnackBar(ft.Text("账号不得为空"), open=True)
            await page.update_async()
            return
        if not password:
            page.snack_bar = ft.SnackBar(ft.Text("密码不得为空"), open=True)
            await page.update_async()
            return

        # 显示加载状态
        login_button.text = "登录中..."
        login_button.disabled = True
        await page.update_async()

        try:
            # 记住密码
            if remember_cb.value:
                await page.client_storage.set_async("username", username)
                await page.client_storage.set_async("password", password)
                await page.client_storage.set_async("remember_flag", "1")

            result = await login(username, password)

            # 存储 token 和 userInfo
            app_state.token = result.get("token", "")
            app_state.user_info = result.get("userInfo", {})
            await app_state.save_to_storage(page)

            # 跳转首页
            await page.go_async("/home")

        except Exception as ex:
            page.snack_bar = ft.SnackBar(
                ft.Text(str(ex) or "服务器报错，请重试！"),
                open=True,
            )
            await page.update_async()
        finally:
            login_button.text = "登录"
            login_button.disabled = False
            await page.update_async()

    login_button.on_click = on_login

    # --- 布局 ---
    # 表单卡片：半透明深色背景
    form_card = ft.Container(
        width=360,
        padding=ft.padding.symmetric(horizontal=30, vertical=30),
        border_radius=12,
        bgcolor=ft.colors.with_opacity(0.3, ft.colors.BLACK),
        content=ft.Column(
            controls=[
                # 标题
                ft.Text(
                    "五位一体",
                    size=40,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=10),
                username_field,
                password_field,
                # 记住密码 + 登录配置
                ft.Row(
                    controls=[remember_cb, login_set_btn],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=10),
                login_button,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
    )

    # 整个页面蓝色背景 + 居中
    page_content = ft.Container(
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=[ft.colors.BLUE_700, ft.colors.BLUE_900],
        ),
        alignment=ft.alignment.center,
        content=form_card,
    )

    return ft.View(
        route="/login",
        controls=[page_content],
        padding=0,
        spacing=0,
    )
