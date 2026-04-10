"""图片上传组件 — 选择图片 → 上传 → 缩略图列表"""

from __future__ import annotations

from typing import Callable, Awaitable

import flet as ft

from services.api_client import api_client
from config import app_config
from utils.app_state import app_state


class ImageUpload(ft.UserControl):
    """图片上传组件。

    参数:
        on_upload_success: async (file_path: str) -> None，上传成功回调
        max_count: 最大上传数量
        disabled: 是否禁用
        initial_images: 已有图片路径列表（服务器相对路径）
    """

    def __init__(
        self,
        page: ft.Page,
        on_upload_success: Callable[[str], Awaitable[None]] | None = None,
        max_count: int = 9,
        disabled: bool = False,
        initial_images: list[str] | None = None,
    ):
        super().__init__()
        self._page = page
        self._on_upload_success = on_upload_success
        self._max_count = max_count
        self._disabled = disabled
        # 存储服务器返回的相对路径
        self._uploaded_paths: list[str] = list(initial_images or [])
        self._file_picker = ft.FilePicker(on_result=self._on_file_picked)
        self._images_row = ft.Row(wrap=True, spacing=8, run_spacing=8)

    @property
    def uploaded_paths(self) -> list[str]:
        """获取已上传图片的相对路径列表"""
        return list(self._uploaded_paths)

    def _get_image_url(self, path: str) -> str:
        """拼接完整图片 URL"""
        if path.startswith("http"):
            return path
        return f"{app_state.host}/jeecg-boot/sys/common/static/{path}"

    def _build_thumbnail(self, path: str) -> ft.Control:
        """构建单张缩略图 + 删除按钮"""

        async def on_delete(e):
            if self._disabled:
                return
            self._uploaded_paths.remove(path)
            self._refresh_images()
            await self.update_async()

        return ft.Stack(
            controls=[
                ft.Container(
                    width=80,
                    height=80,
                    border_radius=6,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    content=ft.Image(
                        src=self._get_image_url(path),
                        fit=ft.ImageFit.COVER,
                        width=80,
                        height=80,
                    ),
                ),
                # 删除按钮
                ft.Container(
                    right=0,
                    top=0,
                    content=ft.IconButton(
                        icon=ft.icons.CANCEL,
                        icon_size=18,
                        icon_color=ft.colors.RED_400,
                        on_click=on_delete,
                    ),
                    visible=not self._disabled,
                ),
            ],
            width=80,
            height=80,
        )

    def _build_add_button(self) -> ft.Control:
        """添加图片按钮"""

        async def on_add(e):
            self._file_picker.pick_files(
                allow_multiple=False,
                allowed_extensions=["jpg", "jpeg", "png", "gif", "bmp"],
                dialog_title="选择图片",
            )

        return ft.Container(
            width=80,
            height=80,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=6,
            alignment=ft.alignment.center,
            on_click=on_add,
            ink=True,
            content=ft.Column(
                controls=[
                    ft.Icon(ft.icons.ADD_A_PHOTO, color=ft.colors.GREY_400, size=28),
                    ft.Text("上传", size=11, color=ft.colors.GREY_400),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        )

    def _refresh_images(self):
        """刷新图片缩略图列表"""
        self._images_row.controls.clear()
        for p in self._uploaded_paths:
            self._images_row.controls.append(self._build_thumbnail(p))
        # 添加按钮
        if not self._disabled and len(self._uploaded_paths) < self._max_count:
            self._images_row.controls.append(self._build_add_button())

    async def _on_file_picked(self, e: ft.FilePickerResultEvent):
        """文件选择回调 → 上传到服务器"""
        if not e.files:
            return

        file = e.files[0]
        # 显示上传中提示
        self._page.snack_bar = ft.SnackBar(ft.Text("上传中..."), open=True)
        await self._page.update_async()

        try:
            result = await api_client.upload(
                app_config.UPLOAD_PATH,
                file.path,
                field_name="file",
            )
            # result 通常是文件相对路径字符串
            file_path = result if isinstance(result, str) else result.get("message", "")
            self._uploaded_paths.append(file_path)
            self._refresh_images()

            self._page.snack_bar = ft.SnackBar(ft.Text("上传成功"), open=True)
            await self._page.update_async()
            await self.update_async()

            if self._on_upload_success:
                await self._on_upload_success(file_path)

        except Exception as ex:
            self._page.snack_bar = ft.SnackBar(ft.Text(f"上传失败：{ex}"), open=True)
            await self._page.update_async()

    def build(self):
        # 将 FilePicker 添加到 page overlay
        if self._file_picker not in self._page.overlay:
            self._page.overlay.append(self._file_picker)

        self._refresh_images()

        return ft.Container(
            content=self._images_row,
            padding=ft.padding.symmetric(vertical=8),
        )
