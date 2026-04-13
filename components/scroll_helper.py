"""滚动行为辅助：Flet 0.25 无 ScrollPhysics，用事件 + scroll_to 禁用 overscroll bounce。"""

from __future__ import annotations

import flet as ft


def apply_no_bounce(lv: ft.ListView) -> ft.ListView:
    """给 ListView 附加禁用顶部/底部过度滚动的处理。"""
    state = {"clamping": False, "user": lv.on_scroll}

    async def _on_scroll(e: ft.OnScrollEvent):
        if state["clamping"]:
            return
        pixels = e.pixels or 0
        max_ext = e.max_scroll_extent or 0
        if pixels > max_ext + 0.5:
            state["clamping"] = True
            try:
                lv.scroll_to(offset=max_ext, duration=0)
            finally:
                state["clamping"] = False
        elif pixels < -0.5:
            state["clamping"] = True
            try:
                lv.scroll_to(offset=0, duration=0)
            finally:
                state["clamping"] = False
        if state["user"]:
            res = state["user"](e)
            if hasattr(res, "__await__"):
                await res

    lv.on_scroll = _on_scroll
    if lv.on_scroll_interval is None:
        lv.on_scroll_interval = 0
    return lv
