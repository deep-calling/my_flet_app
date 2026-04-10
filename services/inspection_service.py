"""电子巡检模块 API"""

from __future__ import annotations

from typing import Any

from services.api_client import api_client


# 巡检任务列表
async def get_record_list(params: dict) -> Any:
    """巡检任务分页列表。params: status, name, pageNo, pageSize"""
    return await api_client.get("/jeecg-boot/app/epi/recordList", params=params)


# 任务详情
async def get_record_detail(record_id: str) -> Any:
    """巡检任务详情"""
    result = await api_client.get(
        "/jeecg-boot/app/epi/record", params={"id": record_id}
    )
    # 接口返回 {records: [...]}, 取第一条
    if isinstance(result, dict):
        records = result.get("records", [])
        return records[0] if records else {}
    return result


# 巡检统计
async def get_record_count(record_id: str) -> Any:
    """巡检统计（toDoItemCount/finishItemCount/toDoContentCount/finishContentCount）"""
    return await api_client.get(
        "/jeecg-boot/app/epi/recordCount", params={"recordId": record_id}
    )


# 点位列表
async def get_item_list(params: dict) -> Any:
    """通过任务id分页查询点位。params: recordId, pageNo, pageSize"""
    return await api_client.get("/jeecg-boot/app/epi/itemList", params=params)


# 检查内容列表
async def get_content_list(params: dict) -> Any:
    """通过点位id分页查询检查内容。params: recordItemId, pageNo, pageSize"""
    return await api_client.get("/jeecg-boot/app/epi/contentList", params=params)


# 开始巡检
async def start_record(record_id: str) -> Any:
    """开始巡检"""
    return await api_client.get(
        "/jeecg-boot/app/epi/startRecord", params={"recordId": record_id}
    )


# 点位签到
async def sign_in(item_id: str) -> Any:
    """检查点位签到"""
    return await api_client.get(
        "/jeecg-boot/app/epi/signIn", params={"itemId": item_id}
    )


# 检查内容提交（正常/异常）
async def submit_content(params: dict) -> Any:
    """提交检查内容。params: sfyc (0正常/1异常), contentId"""
    return await api_client.get("/jeecg-boot/app/epi/submitContent", params=params)


# 提交点位检查结果
async def submit_item(item_id: str) -> Any:
    """提交点位检查结果"""
    return await api_client.get(
        "/jeecg-boot/app/epi/submitItem", params={"itemId": item_id}
    )


# 提交检查结论（完成巡检）
async def check_finish(data: dict) -> Any:
    """提交检查结论。data: id, jcjl, xczp"""
    return await api_client.post("/jeecg-boot/app/epi/checkFinish", json=data)


# 隐患上报
async def epi_report(data: dict) -> Any:
    """巡检中隐患上报。data: recordId, fxsj, yhbz, xczp"""
    return await api_client.post("/jeecg-boot/app/epi/report", json=data)


# 获取巡检签到类型（1=二维码, 2=NFC, 其他=都支持）
async def get_item_check_type() -> Any:
    """获取巡检签到类型字典"""
    return await api_client.get(
        "/jeecg-boot/app/epi/itemCheckType",
        params={"dictCode": "tb_epi_check_type"},
    )


# 扫描二维码获取点位
async def scan_qr_code(qr_id: str) -> Any:
    """扫描二维码获取点位信息"""
    return await api_client.get(
        "/jeecg-boot/app/epi/scanQRCode", params={"id": qr_id}
    )


# 校验二维码
async def check_qr_code(params: dict) -> Any:
    """校验二维码。params: recordItemId, QRMessage"""
    return await api_client.get("/jeecg-boot/app/epi/checkQRCode", params=params)


# 校验NFC
async def verify_nfc_message(params: dict) -> Any:
    """校验NFC。params: recordItemId, nfcMessage"""
    return await api_client.get(
        "/jeecg-boot/app/nfc/verifyNFCMessage", params=params
    )
