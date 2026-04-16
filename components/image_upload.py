"""图片上传组件 — 选择图片 → 上传 → 缩略图列表"""

from __future__ import annotations

from typing import Callable, Awaitable

import flet as ft

from services.api_client import api_client
from config import app_config
from utils.app_state import app_state
from utils.logger import get_logger

log = get_logger("image_upload")


def _acquire_file_picker(
    page: ft.Page,
    on_result: Callable[[ft.FilePickerResultEvent], Awaitable[None]],
) -> ft.FilePicker:
    """复用 Page 级别的 FilePicker，避免每个组件都往 overlay 塞一个、导致泄漏。"""
    picker: ft.FilePicker | None = getattr(page, "_shared_file_picker", None)
    if picker is None:
        picker = ft.FilePicker()
        page.overlay.append(picker)
        page._shared_file_picker = picker  # type: ignore[attr-defined]
    picker.on_result = on_result
    return picker


class ImageUpload(ft.Container):
    """图片上传组件（Container 子类）。

    - on_upload_success: async (file_path: str) -> None
    - max_count: 最大上传数量（含已有图片）
    - disabled: 只读模式，仅显示缩略图
    - initial_images: 已有图片相对路径列表
    """

    THUMB_SIZE = 88

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
        self._uploaded_paths: list[str] = [p for p in (initial_images or []) if p]

        self._file_picker = _acquire_file_picker(self._page, self._on_file_picked)

        self._images_row = ft.Row(
            wrap=True,
            spacing=10,
            run_spacing=10,
        )

        self.padding = ft.padding.symmetric(vertical=4)
        self.content = self._images_row
        self._refresh()

    @property
    def uploaded_paths(self) -> list[str]:
        return list(self._uploaded_paths)

    @staticmethod
    def _image_url(path: str) -> str:
        if path.startswith("http"):
            return path
        return f"{app_state.host}/jeecg-boot/sys/common/static/{path}"

    def _build_thumbnail(self, path: str) -> ft.Control:
        def on_delete(_e):
            if self._disabled:
                return
            if path in self._uploaded_paths:
                self._uploaded_paths.remove(path)
            self._refresh()
            self.update()

        def on_preview(_e):
            dlg = ft.AlertDialog(
                content=ft.Image(
                    src=self._image_url(path),
                    fit=ft.ImageFit.CONTAIN,
                    width=600,
                    height=600,
                ),
            )
            self._page.dialog = dlg
            dlg.open = True
            self._page.update()

        img = ft.Container(
            width=self.THUMB_SIZE,
            height=self.THUMB_SIZE,
            border_radius=6,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            ink=True,
            on_click=on_preview,
            content=ft.Image(
                src=self._image_url(path),
                fit=ft.ImageFit.COVER,
                width=self.THUMB_SIZE,
                height=self.THUMB_SIZE,
                error_content=ft.Container(
                    bgcolor=ft.colors.GREY_200,
                    alignment=ft.alignment.center,
                    content=ft.Icon(ft.icons.BROKEN_IMAGE, color=ft.colors.GREY_500),
                ),
            ),
        )

        if self._disabled:
            return img

        delete_btn = ft.Container(
            right=-6,
            top=-6,
            width=22,
            height=22,
            bgcolor=ft.colors.RED_400,
            border_radius=11,
            alignment=ft.alignment.center,
            ink=True,
            on_click=on_delete,
            content=ft.Icon(
                ft.icons.CLOSE,
                size=14,
                color=ft.colors.WHITE,
            ),
        )

        return ft.Stack(
            controls=[img, delete_btn],
            width=self.THUMB_SIZE,
            height=self.THUMB_SIZE,
        )

    def _build_add_button(self) -> ft.Control:
        def on_add(_e):
            # 点击时重新绑定回调，避免多个 ImageUpload 共享 picker 时回调被覆盖
            self._file_picker.on_result = self._on_file_picked
            self._file_picker.pick_files(
                allow_multiple=False,
                allowed_extensions=["jpg", "jpeg", "png", "gif", "bmp", "webp"],
                dialog_title="选择图片",
            )

        return ft.Container(
            width=self.THUMB_SIZE,
            height=self.THUMB_SIZE,
            bgcolor=ft.colors.GREY_50,
            border=ft.border.all(1, ft.colors.GREY_400),
            border_radius=6,
            alignment=ft.alignment.center,
            ink=True,
            on_click=on_add,
            content=ft.Column(
                controls=[
                    ft.Icon(ft.icons.ADD_A_PHOTO_OUTLINED, color=ft.colors.GREY_600, size=28),
                    ft.Text("上传", size=11, color=ft.colors.GREY_600),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=2,
                tight=True,
            ),
        )

    def _refresh(self):
        self._images_row.controls = [
            self._build_thumbnail(p) for p in self._uploaded_paths
        ]
        if not self._disabled and len(self._uploaded_paths) < self._max_count:
            self._images_row.controls.append(self._build_add_button())

    def _toast(self, msg: str):
        self._page.snack_bar = ft.SnackBar(ft.Text(msg), open=True)
        self._page.update()

    async def _on_file_picked(self, e: ft.FilePickerResultEvent):
        if not e.files:
            return
        f = e.files[0]
        self._toast("上传中...")
        try:
            if not f.path:
                self._toast("当前模式不支持本地文件上传")
                return
            file_path = await api_client.upload(
                app_config.UPLOAD_PATH,
                f.path,
                field_name="file",
            )
            self._uploaded_paths.append(file_path)
            self._refresh()
            self.update()
            self._toast("上传成功")
            if self._on_upload_success:
                await self._on_upload_success(file_path)
        except Exception as ex:
            log.exception("upload failed")
            self._toast(f"上传失败：{ex}")
