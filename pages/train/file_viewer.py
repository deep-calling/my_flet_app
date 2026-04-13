"""培训资料/学习资料 — 在 App 内浏览（WebView 文档预览，Video 视频播放）。

后端走 JeecgBoot 集成的 kkFileView：
    {host}/preview/onlinePreview?url=base64({host}{file_path})

视频走原生 Video 控件，避免 WebView 触发下载。"""

from __future__ import annotations

import base64
from urllib.parse import quote

import flet as ft

from config import app_config


VIDEO_EXTS = {"mp4", "mov", "m4v", "webm", "ogv", "avi", "mkv"}


def _build_full_path(file_path: str) -> str:
    """拼出文件的完整 URL（兼容 /temp 和静态目录两种形态）。"""
    if file_path.startswith("http://") or file_path.startswith("https://"):
        return file_path
    if "/temp" in file_path or file_path.startswith("/"):
        sep = "" if file_path.startswith("/") else "/"
        return f"{app_config.host}{sep}{file_path}"
    return f"{app_config.host}/jeecg-boot/sys/common/static/{file_path}"


def build_preview_url(file_path: str, base_url: str = "/preview/onlinePreview") -> str:
    """构造 kkFileView 在线预览 URL（对齐 uniapp learnDetailNew.vue）。"""
    full = _build_full_path(file_path)
    encoded = base64.b64encode(full.encode("utf-8")).decode("ascii")
    return f"{app_config.host}{base_url}?url={quote(encoded, safe='')}"


def is_video(file_path: str) -> bool:
    name = file_path.rsplit("/", 1)[-1]
    if "." not in name:
        return False
    return name.rsplit(".", 1)[-1].lower() in VIDEO_EXTS


async def build_file_viewer_view(
    page: ft.Page,
    *,
    file_path: str,
    title: str = "资料预览",
    preview_base: str = "/preview/onlinePreview",
) -> ft.View:
    """统一资料查看 View。视频走 Video，其它走 WebView 调 kkFileView。"""

    if is_video(file_path):
        media_url = _build_full_path(file_path)
        body: ft.Control = ft.Video(
            playlist=[ft.VideoMedia(resource=media_url)],
            autoplay=True,
            show_controls=True,
            expand=True,
        )
    else:
        url = build_preview_url(file_path, preview_base)
        body = ft.WebView(
            url=url,
            expand=True,
            on_page_started=None,
        )

    return ft.View(
        route="/train/file_viewer",
        appbar=ft.AppBar(title=ft.Text(title), bgcolor=ft.colors.WHITE),
        controls=[ft.Container(content=body, expand=True)],
        padding=0,
        bgcolor=ft.colors.BLACK,
    )
