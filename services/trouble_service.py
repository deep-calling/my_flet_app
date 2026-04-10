"""双重预防模块 API — 隐患排查(trouble) + 包保责任制(bbzrz) + 风险分析"""

from __future__ import annotations

from typing import Any

from services.api_client import api_client


# ============================================================
# 隐患排查任务 (danger record)
# ============================================================

async def get_task_list(params: dict) -> Any:
    """隐患任务列表（trouble/bbzrz 共用，通过 taskType 区分）"""
    return await api_client.get(
        "/jeecg-boot/app/dangerRecord/recordList", params=params
    )


async def get_task_detail(record_id: str) -> Any:
    """隐患任务详情"""
    return await api_client.get(
        "/jeecg-boot/app/dangerRecord/record", params={"id": record_id}
    )


async def get_record_count(record_id: str) -> Any:
    """检查统计（allCount / finishCount / toDoCount / overdueCount）"""
    return await api_client.get(
        "/jeecg-boot/app/dangerRecord/recordCount", params={"id": record_id}
    )


async def get_entry_list(params: dict) -> Any:
    """检查条目分页列表"""
    return await api_client.get(
        "/jeecg-boot/app/dangerRecord/entryList", params=params
    )


async def get_item_list(params: dict) -> Any:
    """检查项列表"""
    return await api_client.get(
        "/jeecg-boot/app/dangerRecord/itemList", params=params
    )


async def submit_content(params: dict) -> Any:
    """提交检查内容"""
    return await api_client.get(
        "/jeecg-boot/app/dangerRecord/submitContent", params=params
    )


async def check_finish(data: dict) -> Any:
    """提交检查结论"""
    return await api_client.post(
        "/jeecg-boot/app/dangerRecord/checkFinish", json=data
    )


async def check_report(data: dict) -> Any:
    """隐患上报（检查中上报）"""
    return await api_client.post(
        "/jeecg-boot/app/dangerRecord/report", json=data
    )


async def get_danger_dict(dict_code: str) -> Any:
    """获取隐患相关字典"""
    return await api_client.get(
        "/jeecg-boot/app/dangerRecord/dict", params={"dictCode": dict_code}
    )


# ============================================================
# 排查记录 (check record)
# ============================================================

async def get_check_record_list(params: dict, module_type: str = "trouble") -> Any:
    """排查记录列表。module_type: 'trouble' 或 'bbzrz'"""
    path = (
        "/jeecg-boot/app/dangerRecord/checkRecordList"
        if module_type == "trouble"
        else "/jeecg-boot/app/dangerRecord/bbzrzCheckRecordList"
    )
    return await api_client.get(path, params=params)


async def get_check_record_detail(record_id: str) -> Any:
    """排查记录详情"""
    return await api_client.get(
        "/jeecg-boot/danger/riskcheckrecord/riskCheckRecord/queryById",
        params={"id": record_id},
    )


async def update_check_record(data: dict) -> Any:
    """更新排查记录"""
    return await api_client.put(
        "/jeecg-boot/danger/riskcheckrecord/riskCheckRecord/edit", json=data
    )


# ============================================================
# 隐患整改 (rectification)
# ============================================================

async def get_rect_list(params: dict) -> Any:
    """整改台账列表"""
    return await api_client.get(
        "/jeecg-boot/app/dangerRect/list", params=params
    )


async def add_rect(data: dict) -> Any:
    """新增整改"""
    return await api_client.post(
        "/jeecg-boot/app/dangerRect/add", json=data
    )


async def get_rect_detail(record_id: str) -> Any:
    """整改详情"""
    result = await api_client.get(
        "/jeecg-boot/app/dangerRect/queryPageById", params={"id": record_id}
    )
    if isinstance(result, dict):
        records = result.get("records", [])
        if records:
            return records[0]
    return result or {}


async def rect_danger(data: dict) -> Any:
    """整改处理"""
    return await api_client.post(
        "/jeecg-boot/app/dangerRect/rect", json=data
    )


async def yan_shou_danger(data: dict) -> Any:
    """验收处理"""
    return await api_client.post(
        "/jeecg-boot/app/dangerRect/yanShou", json=data
    )


async def check_zgr(params: dict) -> Any:
    """校验是否为整改责任人"""
    return await api_client.get(
        "/jeecg-boot/danger/rect/tbHiddenDangerCheckRectification/checkZgr",
        params=params,
    )


async def check_ysr(params: dict) -> Any:
    """校验是否为验收人"""
    return await api_client.get(
        "/jeecg-boot/danger/rect/tbHiddenDangerCheckRectification/checkYsr",
        params=params,
    )


async def get_act_mode_view(params: dict) -> Any:
    """获取移动端表单视图 URL"""
    return await api_client.get(
        "/jeecg-boot/app/dangerRect/getActModeView", params=params
    )


# ============================================================
# 隐患上报 / 随手拍 (snapshot)
# ============================================================

async def get_snapshot_list(params: dict) -> Any:
    """随手拍列表"""
    return await api_client.get(
        "/jeecg-boot/app/snapshot/list", params=params
    )


async def get_snapshot_detail(snapshot_id: str) -> Any:
    """随手拍详情"""
    return await api_client.get(
        "/jeecg-boot/app/snapshot/snapshot", params={"id": snapshot_id}
    )


async def add_snapshot(data: dict) -> Any:
    """新增随手拍"""
    return await api_client.post(
        "/jeecg-boot/app/snapshot/add", json=data
    )


# ============================================================
# 风险分析 (risk analysis)
# ============================================================

async def get_risk_object_list(params: dict) -> Any:
    """风险分析对象列表"""
    return await api_client.get(
        "/jeecg-boot/doublecontrolprevent/riskanalysisobject/riskAnalysisObject/list",
        params=params,
    )


async def get_risk_object_detail(record_id: str) -> Any:
    """风险分析对象详情"""
    result = await api_client.get(
        "/jeecg-boot/doublecontrolprevent/riskanalysisobject/riskAnalysisObject/queryPageById",
        params={"id": record_id},
    )
    if isinstance(result, dict):
        records = result.get("records", [])
        if records:
            return records[0]
    return result or {}


async def get_risk_unit_list(params: dict) -> Any:
    """风险分析单元列表"""
    return await api_client.get(
        "/jeecg-boot/doublecontrolprevent/riskanalysisunit/riskAnalysisUnit/list",
        params=params,
    )


async def get_risk_unit_detail(record_id: str) -> Any:
    """风险分析单元详情"""
    result = await api_client.get(
        "/jeecg-boot/doublecontrolprevent/riskanalysisunit/riskAnalysisUnit/queryPageById",
        params={"id": record_id},
    )
    if isinstance(result, dict):
        records = result.get("records", [])
        if records:
            return records[0]
    return result or {}


async def get_risk_event_list(params: dict) -> Any:
    """风险分析事件列表"""
    return await api_client.get(
        "/jeecg-boot/doublecontrolprevent/riskanalysisevent/riskAnalysisEvent/list",
        params=params,
    )


async def get_risk_measure_list(params: dict) -> Any:
    """风险管控措施列表"""
    return await api_client.get(
        "/jeecg-boot/doublecontrolprevent/riskmanagemeasure/riskManageMeasure/list",
        params=params,
    )


async def get_risk_measure_detail(record_id: str) -> Any:
    """风险管控措施详情"""
    result = await api_client.get(
        "/jeecg-boot/doublecontrolprevent/riskmanagemeasure/riskManageMeasure/queryPageById",
        params={"id": record_id},
    )
    if isinstance(result, dict):
        records = result.get("records", [])
        if records:
            return records[0]
    return result or {}


async def get_risk_measure_by_object(object_id: str) -> Any:
    """根据风险对象 ID 获取管控措施"""
    return await api_client.get(
        "/jeecg-boot/doublecontrolprevent/riskmanagemeasure/riskManageMeasure/queryByRiskAnalysisObjectId",
        params={"id": object_id},
    )


# ============================================================
# 通用字典
# ============================================================

async def get_dict_items(dict_code: str) -> Any:
    """获取系统字典项"""
    return await api_client.get(
        f"/jeecg-boot/sys/dict/getDictItems/{dict_code}"
    )


# ============================================================
# 人员列表（用于选人）
# ============================================================

async def get_people_list(params: dict | None = None) -> Any:
    """人员列表（整改责任人/发现人选择用）"""
    return await api_client.get(
        "/jeecg-boot/person/tbBasePersonInfo/list3",
        params={"auditStatus": "2", **(params or {})},
    )
