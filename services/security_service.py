"""安全风险分区分级模块 API"""

from __future__ import annotations

from typing import Any

from services.api_client import api_client


# ============================================================
# 应知卡
# ============================================================

async def know_card_list(params: dict) -> Any:
    return await api_client.get("/jeecg-boot/app/risk/knowCardList", params=params)


async def query_know_card_by_id(record_id: str) -> Any:
    return await api_client.get("/jeecg-boot/app/risk/queryKnowCardById", params={"id": record_id})


# ============================================================
# 应急卡
# ============================================================

async def emergency_card_list(params: dict) -> Any:
    return await api_client.get("/jeecg-boot/app/risk/emergencyCardList", params=params)


async def query_emergency_card_by_id(record_id: str) -> Any:
    return await api_client.get("/jeecg-boot/app/risk/queryEmergencyCardById", params={"id": record_id})


# ============================================================
# 承诺卡
# ============================================================

async def commitment_card_list(params: dict) -> Any:
    return await api_client.get("/jeecg-boot/app/risk/commitmentCardList", params=params)


async def query_commitment_card_by_id(record_id: str) -> Any:
    return await api_client.get("/jeecg-boot/app/risk/queryCommitmentCardById", params={"id": record_id})


# ============================================================
# 管控清单
# ============================================================

async def control_list(params: dict) -> Any:
    return await api_client.get("/jeecg-boot/app/risk/controlList", params=params)


# ============================================================
# 辨识清单
# ============================================================

async def identify_list(params: dict) -> Any:
    return await api_client.get("/jeecg-boot/app/risk/identifyList", params=params)


async def query_identify_by_id(record_id: str) -> Any:
    return await api_client.get("/jeecg-boot/app/risk/queryIdentifyById", params={"id": record_id})


# ============================================================
# 安全管控方法（hazop / jha / lopa / scl）
# ============================================================

_METHOD_DATA_APIS = {
    "hazop": "/jeecg-boot/app/risk/queryHazopData",
    "jha": "/jeecg-boot/app/risk/queryJhaData",
    "lopa": "/jeecg-boot/app/risk/queryLopaData",
    "scl": "/jeecg-boot/app/risk/querySclData",
}

_METHOD_DETAIL_APIS = {
    "hazop": "/jeecg-boot/app/risk/queryHazopPageById",
    "jha": "/jeecg-boot/app/risk/queryJhaPageById",
    "lopa": "/jeecg-boot/app/risk/queryLopaPageById",
    "scl": "/jeecg-boot/app/risk/querySclPageById",
}


async def query_method_data(method: str, record_id: str) -> Any:
    """根据分析方法类型查询数据列表"""
    path = _METHOD_DATA_APIS.get(method)
    if not path:
        raise ValueError(f"未知分析方法: {method}")
    return await api_client.get(path, params={"id": record_id})


async def query_method_detail(method: str, record_id: str) -> Any:
    """根据分析方法类型查询详情"""
    path = _METHOD_DETAIL_APIS.get(method)
    if not path:
        raise ValueError(f"未知分析方法: {method}")
    return await api_client.get(path, params={"id": record_id})


# ============================================================
# 风险点台账
# ============================================================

async def risk_point_list(params: dict) -> Any:
    return await api_client.get("/jeecg-boot/app/risk/queryPointPageById", params=params)


async def query_point_by_id(record_id: str) -> Any:
    return await api_client.get("/jeecg-boot/app/risk/queryPointPageById", params={"id": record_id})


async def query_max_risk_by_id(record_id: str) -> Any:
    return await api_client.get("/jeecg-boot/app/risk/queryMaxRiskById", params={"id": record_id})


# ============================================================
# 风险分区台账
# ============================================================

async def risk_zoning_list(params: dict) -> Any:
    return await api_client.get("/jeecg-boot/app/risk/queryZoningById", params=params)


async def query_zoning_by_id(record_id: str) -> Any:
    return await api_client.get("/jeecg-boot/app/risk/queryZoningById", params={"id": record_id})


async def query_records_page_by_id(record_id: str) -> Any:
    """评价记录"""
    return await api_client.get("/jeecg-boot/app/risk/queryRecordsPageById", params={"id": record_id})


async def query_risk_level_vo_by_id(record_id: str) -> Any:
    """控制风险等级分析"""
    return await api_client.get("/jeecg-boot/app/risk/queryRiskLevelVoById", params={"id": record_id})


async def query_factors_page_by_id(record_id: str) -> Any:
    """风险校正因素"""
    return await api_client.get("/jeecg-boot/app/risk/queryFactorsPageById", params={"id": record_id})


# ============================================================
# 风险研判与承诺公告
# ============================================================

async def announcement_list(params: dict) -> Any:
    return await api_client.get("/jeecg-boot/app/risk/announcementList", params=params)


async def query_announcement_by_id(record_id: str) -> Any:
    return await api_client.get("/jeecg-boot/app/risk/queryAnnouncementById", params={"id": record_id})


async def add_announcement(data: dict) -> Any:
    return await api_client.post("/jeecg-boot/app/risk/addAnnouncement", json=data)


# ============================================================
# 风险研判流程相关
# ============================================================

async def start_process(data: dict) -> Any:
    """发起流程"""
    return await api_client.post(
        "/jeecg-boot/act/process/extActProcess/startMutilProcess", json=data
    )


async def get_biz_process_node_info(params: dict) -> Any:
    return await api_client.get(
        "/jeecg-boot/act/process/extActProcessNode/getBizProcessNodeInfo", params=params
    )


async def get_process_task_trans_info(params: dict) -> Any:
    return await api_client.get(
        "/jeecg-boot/act/task/getProcessTaskTransInfo", params=params
    )


async def get_act_mode_view(params: dict) -> Any:
    return await api_client.get(
        "/jeecg-boot/app/dangerRect/getActModeView", params=params
    )


async def get_biz_his_process_node_info(params: dict) -> Any:
    return await api_client.get(
        "/jeecg-boot/act/process/extActProcessNode/getBizHisProcessNodeInfo", params=params
    )


async def get_his_process_task_trans_info(params: dict) -> Any:
    return await api_client.get(
        "/jeecg-boot/act/task/getHisProcessTaskTransInfo", params=params
    )


async def process_complete(data: dict) -> Any:
    """自定义提交（处理审批）"""
    return await api_client.post(
        "/jeecg-boot/act/task/processComplete", json=data
    )


# ============================================================
# 字典 / 人员
# ============================================================

async def get_yes_no_dict() -> Any:
    """是/否字典"""
    return await api_client.get("/jeecg-boot/sys/dict/getDictItems/yes_no")


async def get_security_level_dict() -> Any:
    """风险等级字典"""
    return await api_client.get("/jeecg-boot/sys/dict/getDictItems/tb_security_fxjb")


async def get_person_list() -> Any:
    """人员列表"""
    return await api_client.get(
        "/jeecg-boot/person/tbBasePersonInfo/list3",
        params={"auditStatus": "2"},
    )


# 风险点台账和风险分区台账列表用的是独立的 list 接口
async def risk_point_page_list(params: dict) -> Any:
    """风险点台账分页列表"""
    return await api_client.get("/jeecg-boot/app/risk/pointList", params=params)


async def risk_zoning_page_list(params: dict) -> Any:
    """风险分区台账分页列表"""
    return await api_client.get("/jeecg-boot/app/risk/zoningList", params=params)
