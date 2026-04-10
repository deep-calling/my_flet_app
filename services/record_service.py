"""进出记录 / 摄像头 / 消息 API"""

from __future__ import annotations

from typing import Any

from services.api_client import api_client


# ============================================================
# 进出记录
# ============================================================

async def get_people_record_list(params: dict) -> Any:
    """人员进出记录分页"""
    return await api_client.get(
        "/jeecg-boot/app/personnel/getPeopleAccessRecordPage", params=params
    )


async def get_car_record_list(params: dict) -> Any:
    """车辆进出记录分页"""
    return await api_client.get(
        "/jeecg-boot/app/personnel/getCarAccessRecordPage", params=params
    )


# ============================================================
# 视频监控
# ============================================================

async def get_camera_list(params: dict) -> Any:
    """摄像头分页列表"""
    return await api_client.get(
        "/jeecg-boot/app/camera/getCameraPage", params=params
    )


# ============================================================
# 消息公告
# ============================================================

async def get_message_list(params: dict) -> Any:
    """消息公告分页列表"""
    return await api_client.get(
        "/jeecg-boot/sys/sysAnnouncementSend/getMyAnnouncementSend",
        params=params,
    )


async def mark_message_read(annt_id: str) -> Any:
    """标记消息已读"""
    return await api_client.put(
        "/jeecg-boot/sys/sysAnnouncementSend/editByAnntIdAndUserId",
        json={"anntId": annt_id},
    )
