"""隐患上报（随手拍）— 列表 + 详情 + 新增弹窗"""

from __future__ import annotations

import flet as ft
from datetime import datetime

from services import trouble_service as ts
from components.image_upload import ImageUpload
from components.detail_page import build_detail_page, detail_section
from components.form_fields import form_item, readonly_field
from components.status_badge import status_badge
from utils.app_state import app_state


async def build_handle_view(
    page: ft.Page,
    module_type: str = "trouble",
    task_record_id: str = "",
) -> ft.View:
    """隐患上报列表 + 新增功能。

    task_record_id: 从任务详情跳转过来时携带的关联 ID
    """
    is_bbzrz = module_type == "bbzrz"
    title = "包保责任制上报" if is_bbzrz else "隐患上报"
    task_type = "1" if is_bbzrz else "0"

    # --- 列表状态 ---
    current_page = [1]
    page_size = 10
    items_data: list[dict] = []
    is_loading = [False]

    list_column = ft.Column(spacing=0, expand=True)
    loading_ring = ft.ProgressRing(width=24, height=24, visible=False)
    load_more_btn = ft.Container(visible=False)
    empty_widget = ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(ft.icons.INBOX_OUTLINED, size=64, color=ft.colors.GREY_300),
                ft.Text("暂无数据", size=14, color=ft.colors.GREY_400),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8,
        ),
        alignment=ft.alignment.center,
        padding=ft.padding.only(top=120),
        visible=False,
    )

    async def _load_data(reset: bool = False):
        if is_loading[0]:
            return
        is_loading[0] = True
        loading_ring.visible = True
        await page.update_async()

        if reset:
            current_page[0] = 1
            items_data.clear()
            list_column.controls.clear()

        try:
            params = {
                "taskType": task_type,
                "pageNo": current_page[0],
                "pageSize": page_size,
            }
            result = await ts.get_snapshot_list(params)
            records = result.get("records", []) if isinstance(result, dict) else []
            total = result.get("total", 0) if isinstance(result, dict) else 0

            for item in records:
                items_data.append(item)

                def _make_click(data):
                    async def _click(e):
                        await page.go_async(
                            f"/{module_type}/handle/detail?id={data['id']}"
                        )
                    return _click

                list_column.controls.append(
                    ft.Container(
                        content=_build_item(item),
                        on_click=_make_click(item),
                        ink=True,
                    )
                )

            has_more = len(items_data) < total
            load_more_btn.visible = has_more
            if has_more:
                load_more_btn.content = ft.TextButton(
                    "加载更多", on_click=_on_load_more,
                    style=ft.ButtonStyle(color=ft.colors.BLUE),
                )
            empty_widget.visible = len(items_data) == 0
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"加载失败：{ex}"), open=True)

        is_loading[0] = False
        loading_ring.visible = False
        await page.update_async()

    async def _on_load_more(e):
        current_page[0] += 1
        await _load_data(reset=False)

    def _build_item(item: dict) -> ft.Control:
        status_text = item.get("yhzt_dictText", "")
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row([
                        ft.Text(
                            f"发现时间：{item.get('fxsj', '-')}",
                            size=14, weight=ft.FontWeight.W_500, expand=True,
                        ),
                        status_badge(status_text) if status_text else ft.Container(),
                    ]),
                    ft.Text(
                        f"来源：{item.get('yhly_dictText', '-')}",
                        size=13, color=ft.colors.GREY_600,
                    ),
                    ft.Text(
                        f"备注：{item.get('yhbz', '-')}",
                        size=12, color=ft.colors.GREY_500,
                        max_lines=2, overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                spacing=4,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200)),
        )

    # --- 新增弹窗 ---
    async def _show_add_dialog(e):
        image_upload = ImageUpload(page, max_count=9)
        remark_field = ft.TextField(
            hint_text="请输入备注说明",
            multiline=True, min_lines=3, max_lines=5,
            border_color=ft.colors.GREY_300, text_size=14,
        )

        async def _save(ev):
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data = {
                "fxsj": now_str,
                "yhbz": remark_field.value or "",
                "taskType": task_type,
            }
            # 关联任务
            if task_record_id:
                data["taskRecordId"] = task_record_id

            # 图片
            paths = image_upload.uploaded_paths
            if paths:
                data["xczp"] = ",".join(paths)

            try:
                await ts.add_snapshot(data)
                page.snack_bar = ft.SnackBar(ft.Text("上报成功"), open=True)
                dlg.open = False
                await page.update_async()
                await _load_data(reset=True)
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"上报失败：{ex}"), open=True)
                await page.update_async()

        async def _cancel(ev):
            dlg.open = False
            await page.update_async()

        dlg = ft.AlertDialog(
            title=ft.Text("新增上报"),
            content=ft.Column(
                controls=[
                    ft.Text("现场照片", size=13, color=ft.colors.GREY_700),
                    image_upload,
                    ft.Container(height=8),
                    ft.Text("备注说明", size=13, color=ft.colors.GREY_700),
                    remark_field,
                ],
                tight=True, spacing=4, width=320,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton("取消", on_click=_cancel),
                ft.TextButton("提交", on_click=_save),
            ],
        )
        page.dialog = dlg
        dlg.open = True
        await page.update_async()

    # 浮动新增按钮
    fab = ft.FloatingActionButton(
        icon=ft.icons.ADD, on_click=_show_add_dialog, bgcolor=ft.colors.BLUE
    )

    scroll_content = ft.ListView(
        controls=[
            list_column,
            ft.Container(
                content=ft.Row([loading_ring], alignment=ft.MainAxisAlignment.CENTER),
                padding=10,
            ),
            load_more_btn,
            empty_widget,
        ],
        expand=True,
    )

    view = ft.View(
        route=f"/{module_type}/handle",
        appbar=ft.AppBar(title=ft.Text(title), bgcolor=ft.colors.WHITE),
        controls=[scroll_content],
        floating_action_button=fab,
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    await _load_data(reset=True)
    return view


# ============================================================
# 隐患上报详情页
# ============================================================

async def build_handle_detail_view(
    page: ft.Page,
    record_id: str,
    module_type: str = "trouble",
) -> ft.View:
    """隐患上报（随手拍）详情页 — 只读展示"""
    is_bbzrz = module_type == "bbzrz"
    title = "包保上报详情" if is_bbzrz else "隐患上报详情"

    async def _load(rid: str) -> dict:
        result = await ts.get_snapshot_detail(rid)
        if isinstance(result, dict):
            # 接口可能返回 records 列表
            records = result.get("records", [])
            if records:
                return records[0]
            return result
        return {}

    def _build_content(data: dict) -> ft.Control:
        # 现场照片
        xczp = data.get("xczp", "")
        photo_controls: list[ft.Control] = []
        if xczp:
            for p in xczp.split(","):
                p = p.strip()
                if not p:
                    continue
                url = (
                    p if p.startswith("http")
                    else f"{app_state.host}/jeecg-boot/sys/common/static/{p}"
                )
                photo_controls.append(
                    ft.Container(
                        width=80, height=80,
                        border_radius=6,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        content=ft.Image(src=url, fit=ft.ImageFit.COVER, width=80, height=80),
                    )
                )

        photo_row = ft.Container(
            content=ft.Row(controls=photo_controls, wrap=True, spacing=8, run_spacing=8),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            bgcolor=ft.colors.WHITE,
        ) if photo_controls else ft.Container()

        section = detail_section("基本信息", [
            readonly_field("发现时间", data.get("fxsj", "")),
            readonly_field("上报人", data.get("sbr_dictText", "")),
            readonly_field("隐患备注", data.get("yhzt_dictText", data.get("yhbz", ""))),
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Text("现场照片", size=14, color=ft.colors.GREY_700, width=100),
                        ]),
                        padding=ft.padding.symmetric(horizontal=16, vertical=10),
                        bgcolor=ft.colors.WHITE,
                    ),
                    photo_row,
                ], spacing=0),
            ) if photo_controls else readonly_field("现场照片", "无"),
            readonly_field("处理意见", data.get("clyj", "")),
            readonly_field("隐患来源", data.get("yhly_dictText", "")),
        ])
        return section

    return await build_detail_page(
        page,
        title=title,
        record_id=record_id,
        on_load_data=_load,
        build_content=_build_content,
    )
