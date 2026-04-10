"""报警处理模块 API — 人员定位 / 监测报警"""

from __future__ import annotations

from typing import Any

from services.api_client import api_client


# ============================================================
# 人员定位报警
# ============================================================

async def get_person_alarm_list(params: dict) -> Any:
    """人员定位报警分页列表"""
    return await api_client.get(
        "/jeecg-boot/app/personAlarm/list", params=params
    )


async def deal_person_alarm(data: dict) -> Any:
    """处理人员定位报警"""
    return await api_client.post(
        "/jeecg-boot/app/personAlarm/dealAlarm", json=data
    )


# ============================================================
# 监测指标报警
# ============================================================

async def get_sensor_alarm_list(params: dict) -> Any:
    """监测指标报警分页列表"""
    return await api_client.get(
        "/jeecg-boot/app/sensorAlarm/list", params=params
    )


async def deal_sensor_alarm(data: dict) -> Any:
    """处理监测指标报警"""
    return await api_client.post(
        "/jeecg-boot/app/sensorAlarm/dealAlarm", json=data
    )
