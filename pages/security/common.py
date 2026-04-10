"""安全风险分区分级 — 通用列表+详情工厂函数

大部分子页面结构一致（分页列表 → 详情），用工厂批量生成。
"""

from __future__ import annotations

from typing import Any, Callable, Awaitable

import flet as ft

from components.list_page import build_list_page
from components.detail_page import build_detail_page, detail_section
from components.form_fields import readonly_field


# ------------------------------------------------------------------
# 通用列表卡片构建
# ------------------------------------------------------------------

def _build_card(fields: list[tuple[str, str]], item: dict) -> ft.Control:
    """根据 fields_config 构建列表卡片。

    fields: [(label, data_key), ...]
    """
    rows: list[ft.Control] = []
    for label, key in fields:
        val = str(item.get(key, "") or "")
        rows.append(
            ft.Row(
                controls=[
                    ft.Text(f"{label}:", size=13, color=ft.colors.BLACK87, weight=ft.FontWeight.W_500),
                    ft.Text(val, size=13, color=ft.colors.GREY_700, expand=True),
                ],
                spacing=4,
            )
        )
    return ft.Container(
        content=ft.Column(controls=rows, spacing=6),
        padding=ft.padding.all(14),
        bgcolor=ft.colors.WHITE,
        border_radius=8,
        margin=ft.margin.only(left=12, right=12, top=8),
    )


# ------------------------------------------------------------------
# 简单详情页内容构建（平铺 key-value）
# ------------------------------------------------------------------

def _build_simple_detail_content(
    detail_fields: list[tuple[str, str]],
    section_title: str = "基本信息",
) -> Callable[[dict], ft.Control]:
    """返回一个 build_content 函数，用于 build_detail_page。"""

    def _builder(data: dict) -> ft.Control:
        fields = [readonly_field(label, str(data.get(key, "") or "-")) for label, key in detail_fields]
        return detail_section(section_title, fields)

    return _builder


# ------------------------------------------------------------------
# 工厂：生成列表页构建函数
# ------------------------------------------------------------------

def make_list_view_builder(
    *,
    title: str,
    list_api: Callable[[dict], Awaitable[Any]],
    list_fields: list[tuple[str, str]],
    detail_route: str,
    show_search: bool = False,
) -> Callable[[ft.Page], Awaitable[ft.View]]:
    """生成 async build_xxx_view(page) 列表页构建函数。

    参数:
        title: 页面标题
        list_api: async (params_dict) -> {records, total} 的 service 函数
        list_fields: [(label, data_key)] 列表卡片展示字段
        detail_route: 点击跳转详情路由，如 "/security/know/detail"
        show_search: 是否显示搜索栏
    """

    async def _builder(page: ft.Page) -> ft.View:
        async def _on_load(page_no: int, page_size: int, filters: dict) -> dict:
            params = {"pageNo": page_no, "pageSize": page_size, **filters}
            result = await list_api(params)
            if isinstance(result, dict):
                return {"records": result.get("records", []), "total": result.get("total", 0)}
            return {"records": [], "total": 0}

        def _build_item(item: dict) -> ft.Control:
            return _build_card(list_fields, item)

        async def _on_click(item: dict) -> None:
            rid = item.get("id", "")
            await page.go_async(f"{detail_route}?id={rid}")

        return await build_list_page(
            page,
            title=title,
            on_load_data=_on_load,
            build_item=_build_item,
            on_item_click=_on_click,
            show_search=show_search,
        )

    return _builder


# ------------------------------------------------------------------
# 工厂：生成简单详情页构建函数
# ------------------------------------------------------------------

def make_simple_detail_view_builder(
    *,
    title: str,
    detail_api: Callable[[str], Awaitable[Any]],
    detail_fields: list[tuple[str, str]],
    section_title: str = "基本信息",
    extract_record: Callable[[Any], dict] | None = None,
) -> Callable[[ft.Page, str], Awaitable[ft.View]]:
    """生成 async build_xxx_detail_view(page, record_id) 详情页构建函数。

    参数:
        extract_record: 自定义数据提取，默认从 result.records[0] 取
    """

    async def _builder(page: ft.Page, record_id: str) -> ft.View:
        async def _on_load(rid: str) -> dict:
            result = await detail_api(rid)
            if extract_record:
                return extract_record(result)
            # 默认：result 是 dict 且有 records 字段
            if isinstance(result, dict):
                records = result.get("records", [])
                if records:
                    return records[0]
            return result if isinstance(result, dict) else {}

        return await build_detail_page(
            page,
            title=title,
            record_id=record_id,
            on_load_data=_on_load,
            build_content=_build_simple_detail_content(detail_fields, section_title),
        )

    return _builder


# ------------------------------------------------------------------
# 工厂：生成自定义详情页构建函数
# ------------------------------------------------------------------

def make_custom_detail_view_builder(
    *,
    title: str,
    on_load: Callable[[str], Awaitable[dict]],
    build_content: Callable[[dict], ft.Control],
) -> Callable[[ft.Page, str], Awaitable[ft.View]]:
    """生成需要自定义加载逻辑和渲染的详情页构建函数。"""

    async def _builder(page: ft.Page, record_id: str) -> ft.View:
        return await build_detail_page(
            page,
            title=title,
            record_id=record_id,
            on_load_data=on_load,
            build_content=build_content,
        )

    return _builder
