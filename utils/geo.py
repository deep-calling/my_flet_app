"""GPS 定位：用 ft.Geolocator 取手机坐标，失败则由调用方走 fallback。"""

from __future__ import annotations

import asyncio
from typing import Optional

import flet as ft

from utils.logger import get_logger

log = get_logger("geo")

# Page 级别复用的 Geolocator（非可视化，挂 overlay）
_GEO_ATTR = "_shared_geolocator"


def _acquire_geolocator(page: ft.Page) -> ft.Geolocator:
    geo: Optional[ft.Geolocator] = getattr(page, _GEO_ATTR, None)
    if geo is None:
        geo = ft.Geolocator()
        page.overlay.append(geo)
        setattr(page, _GEO_ATTR, geo)
    return geo


async def get_phone_location(
    page: ft.Page,
    timeout: float = 6.0,
) -> tuple[float, float] | None:
    """尝试拉手机 GPS，返回 (lng, lat)；任何失败返回 None。

    `timeout` 是本次调用的总耗时预算（权限 + 定位合起来）。
    """
    geo = _acquire_geolocator(page)

    async def _ensure_permission() -> bool:
        try:
            status = await geo.get_permission_status_async(wait_timeout=3)
        except Exception:
            log.exception("get_permission_status failed")
            return False
        if status in (
            ft.GeolocatorPermissionStatus.WHILE_IN_USE,
            ft.GeolocatorPermissionStatus.ALWAYS,
        ):
            return True
        if status == ft.GeolocatorPermissionStatus.DENIED_FOREVER:
            log.warning("location permission denied forever")
            return False
        try:
            new_status = await geo.request_permission_async(wait_timeout=10)
        except Exception:
            log.exception("request_permission failed")
            return False
        return new_status in (
            ft.GeolocatorPermissionStatus.WHILE_IN_USE,
            ft.GeolocatorPermissionStatus.ALWAYS,
        )

    try:
        async def _flow() -> tuple[float, float] | None:
            if not await _ensure_permission():
                return None
            pos = await geo.get_current_position_async(
                accuracy=ft.GeolocatorPositionAccuracy.HIGH,
                wait_timeout=timeout,
            )
            if pos and pos.longitude is not None and pos.latitude is not None:
                return float(pos.longitude), float(pos.latitude)
            return None

        return await asyncio.wait_for(_flow(), timeout=timeout + 1)
    except asyncio.TimeoutError:
        log.warning("phone GPS timed out after %.1fs", timeout)
        return None
    except Exception:
        log.exception("phone GPS failed")
        return None
