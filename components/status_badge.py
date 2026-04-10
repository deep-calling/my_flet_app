"""状态标签 — 带圆角背景色的状态显示"""

import flet as ft

# 预定义状态 → 颜色映射
STATUS_COLORS: dict[str, tuple[str, str]] = {
    # (背景色, 文字色)
    "待处理": (ft.colors.ORANGE_50, ft.colors.ORANGE_700),
    "处理中": (ft.colors.BLUE_50, ft.colors.BLUE_700),
    "已完成": (ft.colors.GREEN_50, ft.colors.GREEN_700),
    "已关闭": (ft.colors.GREY_200, ft.colors.GREY_600),
    "已驳回": (ft.colors.RED_50, ft.colors.RED_700),
    "已通过": (ft.colors.GREEN_50, ft.colors.GREEN_700),
    "待审批": (ft.colors.ORANGE_50, ft.colors.ORANGE_700),
    "待整改": (ft.colors.RED_50, ft.colors.RED_700),
    "已整改": (ft.colors.GREEN_50, ft.colors.GREEN_700),
    "待验收": (ft.colors.PURPLE_50, ft.colors.PURPLE_700),
    "已验收": (ft.colors.GREEN_50, ft.colors.GREEN_700),
    "未开始": (ft.colors.GREY_200, ft.colors.GREY_600),
    "进行中": (ft.colors.BLUE_50, ft.colors.BLUE_700),
    "已过期": (ft.colors.RED_50, ft.colors.RED_700),
    "正常": (ft.colors.GREEN_50, ft.colors.GREEN_700),
    "异常": (ft.colors.RED_50, ft.colors.RED_700),
}


def status_badge(
    text: str,
    bgcolor: str | None = None,
    color: str | None = None,
) -> ft.Container:
    """返回状态标签控件。

    如果未指定颜色，会根据 text 自动匹配预定义颜色；
    无匹配时使用蓝色默认样式。
    """
    if bgcolor is None or color is None:
        default_bg, default_fg = STATUS_COLORS.get(
            text, (ft.colors.BLUE_50, ft.colors.BLUE_700)
        )
        bgcolor = bgcolor or default_bg
        color = color or default_fg

    return ft.Container(
        content=ft.Text(text, size=11, color=color),
        bgcolor=bgcolor,
        border_radius=4,
        padding=ft.padding.symmetric(horizontal=8, vertical=2),
    )
