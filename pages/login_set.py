"""登录配置页 — 设置服务器 IP 和端口"""

import flet as ft

from config import app_config
from utils.app_state import app_state


async def build_login_set_view(page: ft.Page) -> ft.View:
    """构建登录配置页视图"""

    # 从 client_storage 读取已保存的 IP/端口
    saved_ip = await page.client_storage.get_async("base_ip") or ""
    saved_port = await page.client_storage.get_async("base_port") or ""

    ip_field = ft.TextField(
        label="IP",
        hint_text="请输入IP",
        value=saved_ip,
        autofocus=True,
    )

    port_field = ft.TextField(
        label="端口",
        hint_text="默认80端口",
        value=saved_port,
    )

    async def on_save(e):
        ip = ip_field.value.strip().rstrip("/")
        if not ip:
            page.snack_bar = ft.SnackBar(ft.Text("IP不能为空"), open=True)
            await page.update_async()
            return

        port = port_field.value.strip() or "80"

        # 持久化到 client_storage
        await page.client_storage.set_async("base_ip", ip)
        await page.client_storage.set_async("base_port", port)

        # 更新全局状态
        host = f"http://{ip}:{port}"
        app_state.host = host
        app_config.host = host

        page.snack_bar = ft.SnackBar(ft.Text("设置成功"), open=True)
        await page.update_async()

        # 延迟返回上一页
        import asyncio
        await asyncio.sleep(1)
        page.views.pop()
        top_view = page.views[-1]
        await page.go_async(top_view.route)

    async def on_back(e):
        page.views.pop()
        top_view = page.views[-1]
        await page.go_async(top_view.route)

    return ft.View(
        route="/login_set",
        appbar=ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                icon_color=ft.colors.WHITE,
                on_click=on_back,
            ),
            title=ft.Text("登录配置", color=ft.colors.WHITE),
            bgcolor=ft.colors.BLUE,
        ),
        controls=[
            ft.Container(
                padding=ft.padding.symmetric(horizontal=30, vertical=20),
                content=ft.Column(
                    controls=[
                        ip_field,
                        port_field,
                        ft.Container(height=20),
                        ft.ElevatedButton(
                            text="确认",
                            width=300,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=20),
                            ),
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.BLUE,
                            on_click=on_save,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
        ],
    )
