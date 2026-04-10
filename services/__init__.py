"""服务层 — 通用接口"""

from __future__ import annotations

from typing import Any

from services.api_client import api_client


async def get_dict_items(dict_code: str) -> list[dict]:
    """通用字典接口 — 传入 dictCode 返回选项列表

    用法:
        items = await get_dict_items("yes_no")
        # [{"text": "是", "value": "1"}, {"text": "否", "value": "0"}]
    """
    result = await api_client.get(
        f"/jeecg-boot/sys/dict/getDictItems/{dict_code}"
    )
    return result if isinstance(result, list) else []


async def upload_file(file_path: str, field_name: str = "file") -> Any:
    """通用上传接口 — multipart/form-data"""
    return await api_client.upload(
        "/jeecg-boot/sys/common/upload", file_path, field_name
    )
