"""我的 — 个人中心页"""

import flet as ft

from utils.app_state import app_state


async def build_my_content(page: ft.Page) -> ft.Control:
    """构建「我的」页面内容"""

    user_info = app_state.user_info
    realname = user_info.get("realname", "用户")
    org_text = user_info.get("orgCodeTxt", "")
    avatar_url = user_info.get("avatar", "")
    if avatar_url and not avatar_url.startswith("http"):
        avatar_url = f"{app_state.host}/jeecg-boot/sys/common/static/{avatar_url}"

    # --- 头像区域 ---
    avatar_widget = ft.CircleAvatar(
        content=ft.Text(realname[0] if realname else "U", size=32),
        radius=40,
        bgcolor=ft.colors.WHITE24,
        foreground_image_url=avatar_url if avatar_url else None,
    )

    profile_header = ft.Container(
        height=220,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=[ft.colors.BLUE_600, ft.colors.BLUE_800],
        ),
        alignment=ft.alignment.center,
        padding=ft.padding.only(top=30),
        content=ft.Column(
            controls=[
                avatar_widget,
                ft.Container(height=8),
                ft.Text(realname, size=22, weight=ft.FontWeight.W_500, color=ft.colors.WHITE),
                ft.Text(org_text, size=14, color=ft.colors.WHITE70) if org_text else ft.Container(),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        ),
    )

    # --- 功能菜单 ---
    async def go_change_password(e):
        await page.go_async("/my/change_password")

    async def go_about(e):
        await page.go_async("/my/about")

    async def do_logout(e):
        # 清除状态
        app_state.token = ""
        app_state.user_info = {}
        await page.client_storage.remove_async("token")
        await page.client_storage.remove_async("user_info")
        await page.go_async("/login")

    menu_card = ft.Container(
        bgcolor=ft.colors.WHITE,
        border_radius=ft.border_radius.only(top_left=16, top_right=16),
        margin=ft.margin.only(top=-20),
        padding=ft.padding.only(top=20),
        content=ft.Column(
            controls=[
                ft.ListTile(
                    leading=ft.Icon(ft.icons.LOCK_OUTLINE, color=ft.colors.BLUE),
                    title=ft.Text("密码修改"),
                    trailing=ft.Icon(ft.icons.CHEVRON_RIGHT),
                    on_click=go_change_password,
                ),
                ft.Divider(height=1),
                ft.ListTile(
                    leading=ft.Icon(ft.icons.INFO_OUTLINE, color=ft.colors.BLUE),
                    title=ft.Text("关于我们"),
                    trailing=ft.Icon(ft.icons.CHEVRON_RIGHT),
                    on_click=go_about,
                ),
            ],
            spacing=0,
        ),
    )

    logout_btn = ft.Container(
        bgcolor=ft.colors.WHITE,
        margin=ft.margin.only(top=12),
        content=ft.Container(
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(vertical=14),
            on_click=do_logout,
            ink=True,
            content=ft.Text("退出登录", size=16, color=ft.colors.BLUE, text_align=ft.TextAlign.CENTER),
        ),
    )

    return ft.Column(
        controls=[
            profile_header,
            menu_card,
            logout_btn,
        ],
        spacing=0,
        expand=True,
    )
