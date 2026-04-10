"""消息公告 — 列表页（未读/已读切换 + 弹窗查看详情）"""

from __future__ import annotations

import flet as ft

from components.list_page import build_list_page
from services import record_service as rs


def _msg_category_text(val) -> str:
    """消息类型映射"""
    mapping = {"1": "通知公告", "2": "系统消息"}
    return mapping.get(str(val), str(val))


async def build_message_view(page: ft.Page) -> ft.View:
    """消息列表，未读/已读切换，点击弹窗查看内容"""

    read_flag = [0]  # 0=未读, 1=已读

    async def _load(page_no: int, page_size: int, filters: dict) -> dict:
        return await rs.get_message_list({
            "pageNo": page_no,
            "pageSize": page_size,
            "readFlag": read_flag[0],
        })

    def _build_item(item: dict) -> ft.Control:
        return ft.Container(
            bgcolor=ft.colors.WHITE,
            border_radius=8,
            padding=ft.padding.all(14),
            margin=ft.margin.only(left=12, right=12, top=8),
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Text(f"标题: {item.get('titile', '-')}", size=14, color=ft.colors.BLACK87),
                    ft.Text(f"消息类型: {_msg_category_text(item.get('msgCategory', ''))}", size=13, color=ft.colors.GREY_600),
                    ft.Row([
                        ft.Text(f"发布人: {item.get('sender', '-')}", size=13, color=ft.colors.GREY_600),
                    ]),
                    ft.Text(f"发布时间: {item.get('sendTime', '-')}", size=13, color=ft.colors.GREY_600),
                ],
            ),
        )

    async def _on_click(item: dict):
        # 如果未读，先标记已读
        if item.get("readFlag") == 0 or item.get("readFlag") == "0":
            try:
                await rs.mark_message_read(item.get("anntId", ""))
            except Exception:
                pass

        # 弹窗显示消息内容
        content_text = item.get("msgContent", "暂无内容")
        dlg = ft.AlertDialog(
            title=ft.Text("通知消息"),
            content=ft.Container(
                content=ft.Text(content_text, size=14),
                height=300,
                width=400,
            ),
            open=True,
        )
        page.dialog = dlg
        await page.update_async()

    view = await build_list_page(
        page,
        title="信息公告",
        on_load_data=_load,
        build_item=_build_item,
        on_item_click=_on_click,
        show_search=False,
    )

    # 插入未读/已读 Tab 栏
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[ft.Tab(text="未读"), ft.Tab(text="已读")],
        height=42,
    )

    async def _on_tab_change(e):
        read_flag[0] = tabs.selected_index
        await view.reload()

    tabs.on_change = _on_tab_change

    body_col = view.controls[0]
    body_col.controls.insert(0, ft.Container(
        content=tabs,
        bgcolor=ft.colors.WHITE,
    ))

    return view
