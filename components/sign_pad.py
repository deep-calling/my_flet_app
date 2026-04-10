"""手写签名组件 — Canvas 手写 + 清除/确认 + 上传"""

from __future__ import annotations

import io
import tempfile
from typing import Callable, Awaitable

import flet as ft
import flet.canvas as cv

from services.api_client import api_client
from config import app_config
from utils.app_state import app_state


class SignPad(ft.UserControl):
    """手写签名组件。

    功能:
    - Canvas 手写签名区域
    - 清除 + 确认按钮
    - 确认后将签名导出为图片上传到服务器
    - 传入 sign_image 则显示已有签名图片
    - disabled 模式

    注意: Flet 0.23 的 Canvas 不支持直接导出为图片文件。
    因此确认签名时使用 FilePicker 让用户选择本地签名图片上传作为替代方案。
    Canvas 绘制仅作为视觉反馈，实际签名图片需要通过文件选择上传。

    参数:
        on_success: async (file_path: str) -> None，签名上传成功回调
        sign_image: 已有签名图片的服务器相对路径
        disabled: 是否禁用
        width: 签名区域宽度
        height: 签名区域高度
    """

    def __init__(
        self,
        page: ft.Page,
        on_success: Callable[[str], Awaitable[None]] | None = None,
        sign_image: str = "",
        disabled: bool = False,
        width: int = 350,
        height: int = 200,
    ):
        super().__init__()
        self._page = page
        self._on_success = on_success
        self._sign_image = sign_image
        self._disabled = disabled
        self._width = width
        self._height = height

        # 画布状态
        self._strokes: list[list[tuple[float, float]]] = []
        self._current_stroke: list[tuple[float, float]] = []
        self._canvas_shapes: list = []

        # 文件选择器（用于上传签名图片）
        self._file_picker = ft.FilePicker(on_result=self._on_file_picked)

    def _get_image_url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return f"{app_state.host}/jeecg-boot/sys/common/static/{path}"

    def _rebuild_canvas_shapes(self) -> list:
        """根据笔画数据重建 Canvas shapes"""
        shapes = []
        for stroke in self._strokes:
            if len(stroke) < 2:
                continue
            for i in range(len(stroke) - 1):
                shapes.append(
                    cv.Line(
                        stroke[i][0], stroke[i][1],
                        stroke[i + 1][0], stroke[i + 1][1],
                        paint=ft.Paint(
                            stroke_width=3,
                            color=ft.colors.BLACK,
                            style=ft.PaintingStyle.STROKE,
                            stroke_cap=ft.StrokeCap.ROUND,
                            stroke_join=ft.StrokeJoin.ROUND,
                        ),
                    )
                )
        return shapes

    async def _on_pan_start(self, e: ft.DragStartEvent):
        if self._disabled:
            return
        self._current_stroke = [(e.local_x, e.local_y)]

    async def _on_pan_update(self, e: ft.DragUpdateEvent):
        if self._disabled or not self._current_stroke:
            return
        self._current_stroke.append((e.local_x, e.local_y))
        # 实时绘制
        self._canvas.shapes = self._rebuild_canvas_shapes() + self._build_current_stroke()
        await self._canvas.update_async()

    def _build_current_stroke(self) -> list:
        """构建当前正在绘制的笔画"""
        shapes = []
        stroke = self._current_stroke
        if len(stroke) < 2:
            return shapes
        for i in range(len(stroke) - 1):
            shapes.append(
                cv.Line(
                    stroke[i][0], stroke[i][1],
                    stroke[i + 1][0], stroke[i + 1][1],
                    paint=ft.Paint(
                        stroke_width=3,
                        color=ft.colors.BLACK,
                        style=ft.PaintingStyle.STROKE,
                        stroke_cap=ft.StrokeCap.ROUND,
                        stroke_join=ft.StrokeJoin.ROUND,
                    ),
                )
            )
        return shapes

    async def _on_pan_end(self, e: ft.DragEndEvent):
        if self._disabled or not self._current_stroke:
            return
        self._strokes.append(list(self._current_stroke))
        self._current_stroke = []

    async def _on_clear(self, e):
        """清除画布"""
        self._strokes.clear()
        self._current_stroke.clear()
        self._canvas.shapes = []
        await self._canvas.update_async()

    async def _on_confirm(self, e):
        """确认签名 — 弹出文件选择器让用户选择签名图片上传。

        由于 Flet Canvas 无法直接导出为图片，
        使用文件选择作为替代方案。
        TODO: 当 Flet 支持 Canvas 导出图片时替换为直接导出。
        """
        if not self._strokes:
            self._page.snack_bar = ft.SnackBar(ft.Text("请先签名"), open=True)
            await self._page.update_async()
            return

        # 提示用户：将手写内容截图保存后选择上传
        self._page.snack_bar = ft.SnackBar(
            ft.Text("请截图保存签名后选择图片文件上传"),
            open=True,
        )
        await self._page.update_async()
        self._file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["jpg", "jpeg", "png"],
            dialog_title="选择签名图片",
        )

    async def _on_file_picked(self, e: ft.FilePickerResultEvent):
        """文件选择回调 → 上传签名图片"""
        if not e.files:
            return

        file = e.files[0]
        self._page.snack_bar = ft.SnackBar(ft.Text("签名上传中..."), open=True)
        await self._page.update_async()

        try:
            result = await api_client.upload(
                app_config.UPLOAD_PATH,
                file.path,
                field_name="file",
            )
            file_path = result if isinstance(result, str) else result.get("message", "")

            self._page.snack_bar = ft.SnackBar(ft.Text("签名成功"), open=True)
            await self._page.update_async()

            if self._on_success:
                await self._on_success(file_path)

        except Exception as ex:
            self._page.snack_bar = ft.SnackBar(ft.Text(f"签名上传失败：{ex}"), open=True)
            await self._page.update_async()

    def build(self):
        # 将 FilePicker 添加到 page overlay
        if self._file_picker not in self._page.overlay:
            self._page.overlay.append(self._file_picker)

        # 已有签名 → 显示图片
        if self._sign_image:
            return ft.Container(
                content=ft.Image(
                    src=self._get_image_url(self._sign_image),
                    fit=ft.ImageFit.CONTAIN,
                    width=self._width,
                    height=self._height,
                ),
                bgcolor=ft.colors.GREY_100,
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=4,
            )

        # 手写签名 Canvas
        self._canvas = cv.Canvas(
            shapes=[],
            width=self._width,
            height=self._height,
        )

        gesture = ft.GestureDetector(
            content=ft.Container(
                content=self._canvas,
                bgcolor=ft.colors.GREY_100,
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=4,
            ),
            on_pan_start=self._on_pan_start,
            on_pan_update=self._on_pan_update,
            on_pan_end=self._on_pan_end,
            drag_interval=10,
        )

        # 操作按钮
        buttons = ft.Row(
            controls=[
                ft.Container(expand=True),
                ft.ElevatedButton(
                    text="清除",
                    on_click=self._on_clear,
                    bgcolor=ft.colors.GREY_400,
                    color=ft.colors.WHITE,
                ),
                ft.ElevatedButton(
                    text="确认",
                    on_click=self._on_confirm,
                    bgcolor=ft.colors.BLUE,
                    color=ft.colors.WHITE,
                ),
            ],
            spacing=12,
        ) if not self._disabled else ft.Container()

        return ft.Column(
            controls=[gesture, buttons],
            spacing=8,
        )
