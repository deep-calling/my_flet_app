"""UI 辅助：overlay 清理。

Flet 0.25 里 `page.close(ctrl)` 只把 `ctrl.open=False`，并不会把控件从
`page.overlay` 中移除。重复打开/关闭对话框时，这些失活的控件（包括模态
barrier）会在 overlay 中堆积，导致每次返回时屏幕越来越黑。
"""

from __future__ import annotations

import flet as ft


def cleanup_overlays(page: ft.Page) -> None:
    """移除非共享的 overlay 控件（通常是已关闭的对话框/底部弹层）。"""
    shared = {
        getattr(page, "_shared_file_picker", None),
        getattr(page, "_shared_geolocator", None),
    }
    shared.discard(None)
    for ov in list(page.overlay):
        if ov in shared:
            continue
        try:
            if hasattr(ov, "open"):
                ov.open = False
        except Exception:
            pass
        try:
            page.overlay.remove(ov)
        except ValueError:
            pass


def close_and_remove(page: ft.Page, control: ft.Control) -> None:
    """关闭单个控件并从 overlay 中移除，防止 barrier 堆积。"""
    try:
        if hasattr(control, "open"):
            control.open = False
    except Exception:
        pass
    try:
        page.overlay.remove(control)
    except ValueError:
        pass
