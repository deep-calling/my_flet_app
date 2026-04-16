"""分页结果归一化：把 JeecgBoot 多种返回形状统一成 {records, total}。

后端常见三种形态：
1. {"records": [...], "total": N}            — IPage.pages
2. {"list": [...], "total": N}               — 自定义
3. [ ... ]                                    — 列表（无分页）
"""

from __future__ import annotations

from typing import Any


def as_page(data: Any) -> dict:
    """归一化分页：始终返回 {records: list, total: int}。"""
    if isinstance(data, list):
        return {"records": data, "total": len(data)}
    if not isinstance(data, dict):
        return {"records": [], "total": 0}
    records = data.get("records")
    if records is None:
        records = data.get("list") or data.get("items") or []
    total = data.get("total")
    if total is None:
        total = data.get("totalCount") or len(records)
    try:
        total_int = int(total)
    except (TypeError, ValueError):
        total_int = len(records)
    return {"records": list(records), "total": total_int}


def first_record(data: Any) -> dict:
    """取分页/单表数据的第一条记录（找不到返回 {}）。"""
    page = as_page(data)
    return page["records"][0] if page["records"] else {}
