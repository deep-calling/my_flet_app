"""SCY 安全生产信息化管理平台 — Flet 版入口"""

from __future__ import annotations

import traceback
from urllib.parse import parse_qs

import flet as ft

from config import app_config
from pages.login import build_login_view
from pages.login_set import build_login_set_view
from pages.home import build_home_content
from pages.workbench import build_workbench_content
from pages.my import build_my_content
from pages.routes import resolve as resolve_route
from services.api_client import api_client
from utils.app_state import app_state
from utils.logger import get_logger

log = get_logger("main")

_AUTH_WHITELIST = {"/login", "/login_set"}
_ROOT_ROUTES = {"/login", "/login_set", "/home"}


async def main(page: ft.Page):
    try:
        await _main_inner(page)
    except Exception as ex:
        log.exception("main handler crashed")
        page.controls.clear()
        page.controls.append(
            ft.Column(
                [
                    ft.Text("启动异常", size=20, color=ft.colors.RED),
                    ft.Text(str(ex), selectable=True),
                    ft.Text(traceback.format_exc(), selectable=True, size=12),
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
        )
        await page.update_async()


async def _main_inner(page: ft.Page):
    page.title = "SCY 安全生产信息化管理平台"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.colors.GREY_100

    # 启动时恢复 host 配置
    try:
        saved_ip = await page.client_storage.get_async("base_ip") or ""
        saved_port = await page.client_storage.get_async("base_port") or ""
    except Exception:
        log.exception("read host from client_storage failed")
        saved_ip = ""
        saved_port = ""
    if saved_ip:
        host = f"http://{saved_ip}:{saved_port or '80'}"
        app_state.host = host
        app_config.host = host

    # Tab 内容缓存
    _tab_cache: dict[int, ft.Control] = {}

    def invalidate_tab_cache():
        _tab_cache.clear()

    app_state.invalidate_tab_cache = invalidate_tab_cache

    async def _on_token_expired():
        app_state.token = ""
        app_state.user_info = {}
        invalidate_tab_cache()
        await page.go_async("/login")

    api_client.on_logout = _on_token_expired

    # --- TabBar 主页面框架 ---
    async def build_tabbar_view(selected_index: int = 0) -> ft.View:
        content_area = ft.Container(expand=True)

        if selected_index in _tab_cache:
            content_area.content = _tab_cache[selected_index]
        else:
            if selected_index == 0:
                content_area.content = await build_home_content(page)
            elif selected_index == 1:
                content_area.content = await build_workbench_content(page)
            elif selected_index == 2:
                content_area.content = await build_my_content(page)
            _tab_cache[selected_index] = content_area.content

        async def on_nav_change(e):
            idx = e.control.selected_index
            page.views.clear()
            page.views.append(await build_tabbar_view(idx))
            await page.update_async()

        nav_bar = ft.NavigationBar(
            selected_index=selected_index,
            on_change=on_nav_change,
            bgcolor=ft.colors.WHITE,
            destinations=[
                ft.NavigationDestination(icon=ft.icons.HOME_OUTLINED, selected_icon=ft.icons.HOME, label="首页"),
                ft.NavigationDestination(icon=ft.icons.DASHBOARD_OUTLINED, selected_icon=ft.icons.DASHBOARD, label="工作台"),
                ft.NavigationDestination(icon=ft.icons.PERSON_OUTLINE, selected_icon=ft.icons.PERSON, label="我的"),
            ],
        )

        return ft.View(
            route="/home",
            controls=[content_area],
            navigation_bar=nav_bar,
            padding=0,
            spacing=0,
            bgcolor=ft.colors.GREY_100,
        )

    def _build_placeholder_tabbar_view(selected_index: int = 0) -> ft.View:
        """轻量级 TabBar 占位视图（不加载内容，不发起 API 请求）。"""
        nav_bar = ft.NavigationBar(
            selected_index=selected_index,
            bgcolor=ft.colors.WHITE,
            destinations=[
                ft.NavigationDestination(icon=ft.icons.HOME_OUTLINED, selected_icon=ft.icons.HOME, label="首页"),
                ft.NavigationDestination(icon=ft.icons.DASHBOARD_OUTLINED, selected_icon=ft.icons.DASHBOARD, label="工作台"),
                ft.NavigationDestination(icon=ft.icons.PERSON_OUTLINE, selected_icon=ft.icons.PERSON, label="我的"),
            ],
        )
        view = ft.View(
            route="/home",
            controls=[ft.Container(expand=True)],
            navigation_bar=nav_bar,
            padding=0,
            spacing=0,
            bgcolor=ft.colors.GREY_100,
        )
        view.data = "_placeholder_"
        return view

    def _parse_route(raw: str) -> tuple[str, dict[str, str]]:
        if "?" in raw:
            path, qs = raw.split("?", 1)
            params = dict(parse_qs(qs, keep_blank_values=True))
            return path, {k: v[0] if v else "" for k, v in params.items()}
        return raw, {}

    def _close_lingering_overlays():
        """路由切换或返回时统一清理残留的 Dialog / BottomSheet。"""
        try:
            if page.dialog and getattr(page.dialog, "open", False):
                page.dialog.open = False
        except Exception:
            log.debug("close dialog failed", exc_info=True)
        if page.overlay:
            # 保留共享的 FilePicker / Geolocator（以 _shared_ 前缀标识）
            shared = {
                getattr(page, "_shared_file_picker", None),
                getattr(page, "_shared_geolocator", None),
            }
            shared.discard(None)
            keep = list(shared)
            for ov in list(page.overlay):
                if ov in shared:
                    continue
                try:
                    if hasattr(ov, "open"):
                        ov.open = False
                except Exception:
                    log.debug("overlay close failed", exc_info=True)
            page.overlay.clear()
            for s in keep:
                page.overlay.append(s)

    async def route_change(e: ft.RouteChangeEvent):
        raw_route = page.route
        route, qparams = _parse_route(raw_route)
        _close_lingering_overlays()

        preserve_stack = (
            route not in _ROOT_ROUTES
            and bool(app_state.token)
            and bool(page.views)
            and page.views[0].data == "_placeholder_"
        )
        if not preserve_stack:
            page.views.clear()

        # 登录拦截
        if route not in _AUTH_WHITELIST and not app_state.token:
            page.views.append(await build_login_view(page))
            await page.update_async()
            return

        # 根路由
        if route == "/login":
            page.views.append(await build_login_view(page))
        elif route == "/login_set":
            page.views.append(await build_login_view(page))
            page.views.append(await build_login_set_view(page))
        elif route == "/home":
            page.views.append(await build_tabbar_view(0))
        else:
            spec = resolve_route(route)
            page.views.append(_build_placeholder_tabbar_view(spec.tab_index if spec else 0))
            if spec is not None:
                try:
                    page.views.append(await spec.builder(page, qparams, route))
                except Exception as ex:
                    log.exception("route builder failed: %s", route)
                    page.views.append(
                        ft.View(
                            route=route,
                            appbar=ft.AppBar(title=ft.Text("加载失败")),
                            controls=[
                                ft.Container(
                                    content=ft.Text(f"页面加载失败：{ex}", size=14),
                                    padding=20,
                                ),
                            ],
                        )
                    )

        # 去重占位视图
        if preserve_stack and len(page.views) > 1:
            seen_placeholder = False
            kept: list[ft.View] = []
            for v in page.views:
                if v.data == "_placeholder_":
                    if not seen_placeholder:
                        kept.append(v)
                        seen_placeholder = True
                else:
                    kept.append(v)
            page.views.clear()
            page.views.extend(kept)

        await page.update_async()

    async def view_pop(e: ft.ViewPopEvent):
        _close_lingering_overlays()
        # 取消可能仍在跑的 list_page 首次加载任务
        popping = page.views[-1] if page.views else None
        if popping is not None and isinstance(popping.data, dict):
            task_ref = popping.data.get("load_task")
            if task_ref and task_ref[0] is not None:
                try:
                    task_ref[0].cancel()
                except Exception:
                    log.debug("cancel load_task failed", exc_info=True)

        if len(page.views) > 1:
            page.views.pop()
            if len(page.views) == 1 and page.views[0].route == "/home":
                # 从子页面返回到首页：清掉 Tab 缓存，确保红点/待办刷新
                invalidate_tab_cache()
                page.views.clear()
                page.views.append(await build_tabbar_view(0))
            await page.update_async()

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    await page.go_async("/login")


ft.app(target=main)
