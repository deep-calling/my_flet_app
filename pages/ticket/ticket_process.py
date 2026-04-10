"""作业票处理流程页 — 封装 6 步流程的导航入口

此模块主要作为路由调度器，将不同步骤的操作转发到 ticket_detail 页面。
所有类型共用同一套流程逻辑，差异通过 config 参数化。
"""

from __future__ import annotations

import flet as ft

from pages.ticket.config import get_config_by_type_value
from pages.ticket.ticket_detail import build_ticket_detail_page


async def build_ticket_process_page(
    page: ft.Page,
    ticket_id: str,
    type_value: str,
) -> ft.View:
    """构建作业票处理流程页。

    实际上 detail 和 process 在原项目中结构几乎一致，
    这里直接复用 ticket_detail 页面。
    """
    return await build_ticket_detail_page(page, ticket_id, type_value)
