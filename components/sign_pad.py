"""手写签名组件 — Canvas 手写 + 清除 + 确认上传"""

from __future__ import annotations

import io
from typing import Callable, Awaitable

import flet as ft
import flet.canvas as cv
from PIL import Image, ImageDraw

from services.api_client import api_client
from config import app_config
from utils.app_state import app_state


class SignPad(ft.Container):
    """手写签名组件（Container 子类）。

    - sign_image 非空：只读显示已有签名图片
    - 否则：Canvas 手写 + 清除/确认按钮，确认后渲染 PNG 上传
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
        self._w = width
        self._h = height
        self._strokes: list[list[tuple[float, float]]] = []
        self._current: list[tuple[float, float]] = []

        self.padding = 0
        self.width = width

        if sign_image:
            self._build_readonly_view()
        else:
            self._build_interactive_view()

    @staticmethod
    def _image_url(path: str) -> str:
        if path.startswith("http"):
            return path
        return f"{app_state.host}/jeecg-boot/sys/common/static/{path}"

    def _build_readonly_view(self):
        self.content = ft.Container(
            width=self._w,
            height=self._h,
            bgcolor=ft.colors.GREY_100,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=4,
            alignment=ft.alignment.center,
            content=ft.Image(
                src=self._image_url(self._sign_image),
                fit=ft.ImageFit.CONTAIN,
                width=self._w,
                height=self._h,
            ),
        )

    def _build_interactive_view(self):
        self._canvas = cv.Canvas(
            shapes=[],
            width=self._w,
            height=self._h,
        )

        board = ft.Container(
            width=self._w,
            height=self._h,
            bgcolor=ft.colors.WHITE,
            border=ft.border.all(1, ft.colors.GREY_400),
            border_radius=4,
            content=self._canvas,
        )

        gesture = ft.GestureDetector(
            content=board,
            drag_interval=10,
            on_pan_start=self._on_pan_start,
            on_pan_update=self._on_pan_update,
            on_pan_end=self._on_pan_end,
        )

        if self._disabled:
            self.content = board
            return

        btns = ft.Row(
            controls=[
                ft.Container(expand=True),
                ft.OutlinedButton(
                    "清除",
                    icon=ft.icons.REFRESH,
                    on_click=self._on_clear,
                ),
                ft.ElevatedButton(
                    "确认",
                    icon=ft.icons.CHECK,
                    on_click=self._on_confirm,
                    bgcolor=ft.colors.BLUE,
                    color=ft.colors.WHITE,
                ),
            ],
            spacing=12,
        )

        self.content = ft.Column(
            controls=[gesture, btns],
            spacing=8,
            tight=True,
        )

    def _paint(self) -> ft.Paint:
        return ft.Paint(
            stroke_width=2.5,
            color=ft.colors.BLACK,
            style=ft.PaintingStyle.STROKE,
            stroke_cap=ft.StrokeCap.ROUND,
            stroke_join=ft.StrokeJoin.ROUND,
        )

    def _rebuild_shapes(self) -> list:
        shapes: list = []
        all_strokes = list(self._strokes)
        if self._current:
            all_strokes.append(self._current)
        for stroke in all_strokes:
            if len(stroke) < 2:
                continue
            paint = self._paint()
            for i in range(len(stroke) - 1):
                x0, y0 = stroke[i]
                x1, y1 = stroke[i + 1]
                shapes.append(cv.Line(x0, y0, x1, y1, paint=paint))
        return shapes

    def _on_pan_start(self, e: ft.DragStartEvent):
        if self._disabled:
            return
        self._current = [(e.local_x, e.local_y)]

    def _on_pan_update(self, e: ft.DragUpdateEvent):
        if self._disabled:
            return
        if not self._current:
            self._current = [(e.local_x, e.local_y)]
            return
        self._current.append((e.local_x, e.local_y))
        self._canvas.shapes = self._rebuild_shapes()
        self._canvas.update()

    def _on_pan_end(self, e: ft.DragEndEvent):
        if self._disabled or not self._current:
            return
        self._strokes.append(list(self._current))
        self._current = []

    def _on_clear(self, e):
        self._strokes.clear()
        self._current.clear()
        self._canvas.shapes = []
        self._canvas.update()

    def _render_png(self) -> bytes:
        img = Image.new("RGB", (self._w, self._h), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        for stroke in self._strokes:
            if len(stroke) < 2:
                continue
            for i in range(len(stroke) - 1):
                draw.line([stroke[i], stroke[i + 1]], fill=(0, 0, 0), width=3)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def _toast(self, msg: str):
        self._page.open(ft.SnackBar(ft.Text(msg)))
        self._page.update()

    async def _on_confirm(self, e):
        if not self._strokes:
            self._toast("请先签名")
            return
        self._toast("签名上传中...")
        try:
            png = self._render_png()
            file_path = await api_client.upload_bytes(
                app_config.UPLOAD_PATH,
                png,
                filename=f"sign_{id(self)}.png",
                field_name="file",
                content_type="image/png",
            )
            self._toast("签名成功")
            if self._on_success:
                await self._on_success(file_path)
        except Exception as ex:
            self._toast(f"签名上传失败：{ex}")
