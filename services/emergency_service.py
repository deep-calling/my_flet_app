"""应急演练模块 API — 演练计划 / 应急队伍 / 应急物资"""

from __future__ import annotations

from typing import Any

from services.api_client import api_client


# ============================================================
# 演练计划
# ============================================================

async def get_plan_list(params: dict) -> Any:
    """演练计划分页列表"""
    return await api_client.get(
        "/jeecg-boot/app/emer/planList", params=params
    )


async def get_plan_detail(record_id: str) -> Any:
    """通过 id 查询演练计划详情（Page 对象返回字典）"""
    result = await api_client.get(
        "/jeecg-boot/app/emer/queryPlanPageById", params={"id": record_id}
    )
    records = result.get("records", []) if isinstance(result, dict) else []
    return records[0] if records else {}


# ============================================================
# 应急队伍
# ============================================================

async def get_team_list(params: dict) -> Any:
    """应急队伍分页列表"""
    return await api_client.get(
        "/jeecg-boot/app/emer/teamList", params=params
    )


async def get_team_detail(record_id: str) -> Any:
    """通过 id 查询应急队伍详情"""
    result = await api_client.get(
        "/jeecg-boot/app/emer/queryTeamPageById", params={"id": record_id}
    )
    records = result.get("records", []) if isinstance(result, dict) else []
    return records[0] if records else {}


# ============================================================
# 应急物资
# ============================================================

async def get_material_list(params: dict) -> Any:
    """应急物资分页列表"""
    return await api_client.get(
        "/jeecg-boot/app/emer/materialList", params=params
    )


async def get_material_detail(record_id: str) -> Any:
    """通过 id 查询应急物资详情"""
    result = await api_client.get(
        "/jeecg-boot/app/emer/queryPageById", params={"id": record_id}
    )
    records = result.get("records", []) if isinstance(result, dict) else []
    return records[0] if records else {}


# ============================================================
# 字典
# ============================================================

async def get_dict_items(dict_code: str) -> list[dict]:
    """获取字典选项列表"""
    result = await api_client.get(
        f"/jeecg-boot/sys/dict/getDictItems/{dict_code}"
    )
    return result if isinstance(result, list) else []
