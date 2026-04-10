"""培训考试模块 API"""

from __future__ import annotations

from typing import Any

from services.api_client import api_client
from utils.app_state import app_state


def _username() -> str:
    return app_state.user_info.get("username", "")


def _person_id() -> str:
    return app_state.user_info.get("personId", "")


# ============================================================
# 线下培训
# ============================================================

async def get_offline_train_list(params: dict) -> Any:
    """线下培训列表（type=1 待签到, type=2 已完成）"""
    params.setdefault("username", _username())
    return await api_client.get("/jeecg-boot/app/edu/new/appList", params=params)


async def get_training_detail(training_id: str) -> Any:
    """培训详情"""
    result = await api_client.get(
        "/jeecg-boot/app/edu/new/trainingById", params={"id": training_id}
    )
    records = result.get("records", []) if isinstance(result, dict) else []
    return records[0] if records else {}


async def sign_training(training_id: str) -> Any:
    """签到"""
    return await api_client.post(
        "/jeecg-boot/app/edu/new/sign",
        json={"trainingId": training_id, "username": _username()},
    )


# ============================================================
# 学习资料（旧版在线学习）
# ============================================================

async def get_file_type_dict() -> Any:
    """文件类型字典"""
    return await api_client.get("/jeecg-boot/app/edu/new/fileTypeDict")


async def get_type_dict() -> Any:
    """所属类别字典"""
    return await api_client.get("/jeecg-boot/app/edu/new/typeDict")


async def get_online_learning_list(params: dict) -> Any:
    """学习资料列表"""
    params.setdefault("userId", _person_id())
    return await api_client.get("/jeecg-boot/app/edu/new/onlineLearning", params=params)


async def submit_learning_record(data: dict) -> Any:
    """提交学习记录"""
    data.setdefault("username", _username())
    return await api_client.post("/jeecg-boot/app/edu/new/learning", json=data)


# ============================================================
# 线上培训任务（旧版）
# ============================================================

async def get_training_task_list(params: dict) -> Any:
    """线上培训任务列表"""
    params.setdefault("pxr", _person_id())
    return await api_client.get(
        "/jeecg-boot/app/edu/new/trainingTask",
        params={**params, "column": "wcqk", "order": "desc"},
    )


async def submit_task_record(data: dict) -> Any:
    """提交培训任务学习记录"""
    return await api_client.post("/jeecg-boot/app/edu/new/task", json=data)


# ============================================================
# 线上培训（新版）
# ============================================================

async def get_learn_list_new(params: dict) -> Any:
    """新版线上培训列表"""
    params.setdefault("userId", _person_id())
    return await api_client.get("/jeecg-boot/app/edu/new/appLearnList", params=params)


async def query_learn_record(record_id: str) -> Any:
    """查询学习记录详情"""
    return await api_client.get(
        "/jeecg-boot/edunew/task/tbEduTrainingTask/queryById",
        params={"id": record_id},
    )


async def temp_save_learn_record(data: dict) -> Any:
    """暂存学习记录"""
    return await api_client.put(
        "/jeecg-boot/edunew/task/tbEduTrainingTask/temporary", json=data
    )


async def save_learn_record(data: dict) -> Any:
    """保存学习记录（完成）"""
    return await api_client.put(
        "/jeecg-boot/edunew/task/tbEduTrainingTask/edit", json=data
    )


# ============================================================
# 在线刷题
# ============================================================

async def get_brush_list(params: dict) -> Any:
    """刷题列表"""
    params.setdefault("username", _username())
    return await api_client.get("/jeecg-boot/app/edu/new/brushList", params=params)


async def get_brush_complete_list(params: dict) -> Any:
    """刷题已完成列表"""
    params.setdefault("username", _username())
    return await api_client.get("/jeecg-boot/app/edu/new/brushCompleteList", params=params)


# ============================================================
# 在线考试
# ============================================================

async def get_exam_list(params: dict) -> Any:
    """考试列表（type=1 待处理, type=2 已完成）"""
    params.setdefault("username", _username())
    return await api_client.get("/jeecg-boot/app/edu/new/examList", params=params)


async def get_exam_items(test_paper_id: str, exam_id: str) -> Any:
    """获取试卷题目"""
    return await api_client.get(
        "/jeecg-boot/app/edu/new/examItemsById",
        params={"id": test_paper_id, "examId": exam_id, "username": _username()},
    )


async def confirm_answer(data: dict) -> Any:
    """确认单题答案"""
    data.setdefault("username", _username())
    return await api_client.get("/jeecg-boot/app/edu/new/confirm", params=data)


async def submit_exam(data: dict) -> Any:
    """交卷"""
    data.setdefault("username", _username())
    return await api_client.post("/jeecg-boot/app/edu/new/assignment", json=data)


async def get_analysis(item_id: str) -> Any:
    """获取题目解析"""
    return await api_client.get(
        "/jeecg-boot/app/edu/new/analysisById", params={"id": item_id}
    )


# ============================================================
# 考试结果 / 详情
# ============================================================

async def get_exam_details(exam_id: str, result_id: str = "") -> Any:
    """考试结果详情"""
    params: dict[str, str] = {"examId": exam_id, "username": _username()}
    if result_id:
        params["resultId"] = result_id
    return await api_client.get("/jeecg-boot/app/edu/new/examDetails", params=params)


async def get_exam_item_details(params: dict) -> Any:
    """考试试卷详情（答案解析）"""
    params.setdefault("username", _username())
    return await api_client.get("/jeecg-boot/app/edu/new/examItemDetails", params=params)


async def get_brush_item_details(params: dict) -> Any:
    """刷题试卷详情（答案解析）"""
    params.setdefault("username", _username())
    return await api_client.get("/jeecg-boot/app/edu/new/brushExamItemDetails", params=params)
