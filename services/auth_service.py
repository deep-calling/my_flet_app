"""认证服务 — 登录 / 修改密码"""

from __future__ import annotations

from typing import Any

from services.api_client import api_client


async def login(username: str, password: str) -> Any:
    """调用 POST /jeecg-boot/sys/mLogin，返回 result（含 token + userInfo）"""
    return await api_client.post(
        "/jeecg-boot/sys/mLogin",
        json={"username": username, "password": password},
    )


async def update_password(old_password: str, new_password: str, confirm_password: str) -> Any:
    """调用修改密码接口"""
    return await api_client.put(
        "/jeecg-boot/sys/updatePassword",
        json={
            "oldpassword": old_password,
            "password": new_password,
            "confirmpassword": confirm_password,
        },
    )
