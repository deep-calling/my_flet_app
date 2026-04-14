"""作业票模块 API — 统一 8 种类型的所有接口"""

from __future__ import annotations

from typing import Any

from services.api_client import api_client


# ============================================================
# 通用辅助数据接口
# ============================================================

async def get_dict_work_type() -> Any:
    """获取作业票类型字典"""
    return await api_client.get("/jeecg-boot/app/ticket/getDictWorkType")


async def get_depart_list() -> Any:
    """获取部门树"""
    return await api_client.get(
        "/jeecg-boot/sys/sysDepart/queryTreeList",
        params={"pageNo": 1, "pageSize": 99999},
    )


async def get_people_list() -> Any:
    """获取人员列表"""
    return await api_client.get(
        "/jeecg-boot/person/tbBasePersonInfo/queryList",
        params={"pageNo": 1, "pageSize": 99999},
    )


async def get_people_zs_list(ticket_type: str) -> Any:
    """获取证书人员列表"""
    return await api_client.get(
        "/jeecg-boot/person/tbBasePersonInfo/queryZSList",
        params={"type": ticket_type, "pageNo": 1, "pageSize": 99999},
    )


async def get_camera_list() -> Any:
    """获取摄像头列表"""
    return await api_client.get("/jeecg-boot/camera/tbCameraInfo/listAll")


async def get_dict_items(dict_code: str) -> Any:
    """获取字典项"""
    return await api_client.get(f"/jeecg-boot/sys/dict/getDictItems/{dict_code}")


async def get_qttszyzbh_list(ticket_type: str) -> Any:
    """获取其他特殊作业证编号列表"""
    return await api_client.get(
        "/jeecg-boot/ticketprocess/utils/getZYZBHByZYLB",
        params={"zylb": ticket_type},
    )


async def get_user_zs(ticket_type: str, ids: str) -> Any:
    """按作业类别和人员 ID 批量查询证书编号"""
    return await api_client.get(
        "/jeecg-boot/ticketprocess/utils/getZyzs",
        params={"zylb": ticket_type, "ids": ids},
    )


async def get_table_data(params: dict) -> Any:
    """通用表数据查询（坐标等）"""
    return await api_client.get(
        "/jeecg-boot/ticketprocess/utils/getTableData", params=params
    )


# ============================================================
# 作业票 CRUD（根据类型前缀自动拼接）
# ============================================================

async def ticket_list(api_prefix: str, params: dict) -> Any:
    """作业票列表"""
    return await api_client.get(f"{api_prefix}/list", params=params)


async def ticket_detail(query_path: str, ticket_id: str) -> Any:
    """作业票详情"""
    return await api_client.get(query_path, params={"id": ticket_id})


async def ticket_add(add_path: str, data: dict) -> Any:
    """新增作业票"""
    return await api_client.post(add_path, json=data)


async def ticket_edit(edit_path: str, data: dict) -> Any:
    """编辑作业票"""
    return await api_client.post(edit_path, json=data)


# ============================================================
# 详情页 — 6 步流程接口（通用，根据 api_prefix 区分类型）
# ============================================================

async def get_inspection_by_id(api_prefix: str, ticket_id: str) -> Any:
    """获取安全分析数据"""
    return await api_client.get(
        f"{api_prefix}/getInspectionById", params={"id": ticket_id}
    )


async def add_inspection(api_prefix: str, data: dict) -> Any:
    """新增安全分析"""
    return await api_client.post(f"{api_prefix}/inspectionAdd", json=data)


async def edit_inspection(api_prefix: str, data: dict) -> Any:
    """编辑安全分析"""
    return await api_client.post(f"{api_prefix}/inspectionEdit", json=data)


async def submit_inspection(api_prefix: str, ticket_id: str) -> Any:
    """提交安全分析"""
    return await api_client.post(
        f"{api_prefix}/inspectionSubmit", json={"ticketId": ticket_id}
    )


async def get_dict_harm(api_prefix: str, ticket_id: str) -> Any:
    """获取危害辨识字典"""
    return await api_client.get(
        f"{api_prefix}/getDictHarm", params={"id": ticket_id}
    )


async def get_measure_by_id(api_prefix: str, ticket_id: str) -> Any:
    """获取安全措施列表"""
    return await api_client.get(
        f"{api_prefix}/getMeasureById", params={"id": ticket_id}
    )


async def measures_apply(api_prefix: str, data: dict) -> Any:
    """确认安全措施"""
    return await api_client.post(f"{api_prefix}/measuresApply", json=data)


async def save_assessment(api_prefix: str, data: dict) -> Any:
    """保存安全评估"""
    return await api_client.post(f"{api_prefix}/save", json=data)


async def submit_assessment(api_prefix: str, data: dict) -> Any:
    """提交安全评估"""
    return await api_client.post(f"{api_prefix}/submit", json=data)


async def get_confess(api_prefix: str, ticket_id: str) -> Any:
    """获取安全交底数据"""
    return await api_client.get(
        f"{api_prefix}/getConfess", params={"id": ticket_id}
    )


async def confess_apply(api_prefix: str, data: dict) -> Any:
    """安全交底签名"""
    return await api_client.post(f"{api_prefix}/confessApply", json=data)


async def confess_submit(api_prefix: str, ticket_id: str) -> Any:
    """提交安全交底"""
    return await api_client.get(
        f"{api_prefix}/confessSubmit", params={"id": ticket_id}
    )


async def get_approve(api_prefix: str, ticket_id: str) -> Any:
    """获取审批数据"""
    return await api_client.get(
        f"{api_prefix}/getApprove", params={"id": ticket_id}
    )


async def approve_apply(api_prefix: str, data: dict) -> Any:
    """审批签名"""
    return await api_client.post(f"{api_prefix}/approve", json=data)


async def get_dict_apply_status(api_prefix: str) -> Any:
    """获取审批状态字典"""
    return await api_client.get(f"{api_prefix}/getDictApplyStatus")


async def forward_approve(api_prefix: str, data: dict) -> Any:
    """转办审批"""
    return await api_client.post(f"{api_prefix}/forward", json=data)


async def get_people_list_for_forward(api_prefix: str) -> Any:
    """获取转办人员列表"""
    return await api_client.get(f"{api_prefix}/peopleList")


async def check_begin_btn(api_prefix: str, ticket_id: str, username: str) -> Any:
    """检查是否可以开始作业"""
    return await api_client.get(
        f"{api_prefix}/checkBeginBtn",
        params={"id": ticket_id, "username": username},
    )


async def begin_ticket(api_prefix: str, ticket_id: str) -> Any:
    """开始作业"""
    return await api_client.post(
        f"{api_prefix}/begin", json={"id": ticket_id}
    )


async def pause_ticket(api_prefix: str, ticket_id: str) -> Any:
    """暂停作业"""
    return await api_client.post(
        f"{api_prefix}/pause", json={"id": ticket_id}
    )


async def complete_ticket(api_prefix: str, ticket_id: str) -> Any:
    """完成作业"""
    return await api_client.post(
        f"{api_prefix}/complete", json={"id": ticket_id}
    )


async def get_acceptance(api_prefix: str, ticket_id: str, username: str) -> Any:
    """获取验收数据"""
    return await api_client.get(
        f"{api_prefix}/getAcceptance",
        params={"id": ticket_id, "userName": username},
    )


async def acceptance_submit(api_prefix: str, ticket_id: str) -> Any:
    """提交验收"""
    return await api_client.post(
        f"{api_prefix}/acceptanceSubmit", json={"ticketId": ticket_id}
    )


async def sign_ticket(api_prefix: str, data: dict) -> Any:
    """验收签名"""
    return await api_client.post(f"{api_prefix}/sign", json=data)


async def get_camera_url(api_prefix: str, params: dict) -> Any:
    """获取摄像头播放地址"""
    return await api_client.get(
        "/jeecg-boot/ticketprocess/utils/getZYCamera", params=params
    )


# ============================================================
# 作业申请 CRUD
# ============================================================

_ZYSQ_PREFIX = "/jeecg-boot/ticket/zysq/tbTicketZysq"


async def zysq_list(params: dict) -> Any:
    """作业申请列表"""
    return await api_client.get(f"{_ZYSQ_PREFIX}/list", params=params)


async def zysq_sq_list(params: dict) -> Any:
    """作业申请审核列表"""
    return await api_client.get(f"{_ZYSQ_PREFIX}/sqList", params=params)


async def zysq_detail(record_id: str) -> Any:
    """作业申请详情"""
    return await api_client.get(
        f"{_ZYSQ_PREFIX}/queryById", params={"id": record_id}
    )


async def zysq_add(data: dict) -> Any:
    """新增作业申请"""
    return await api_client.post(f"{_ZYSQ_PREFIX}/add", json=data)


async def zysq_edit(data: dict) -> Any:
    """编辑作业申请"""
    return await api_client.put(f"{_ZYSQ_PREFIX}/edit", json=data)


async def zysq_delete(record_id: str) -> Any:
    """删除作业申请"""
    return await api_client.delete(
        f"{_ZYSQ_PREFIX}/delete", params={"id": record_id}
    )


async def zysq_status(record_id: str) -> Any:
    """作业申请发起/同意"""
    return await api_client.get(
        f"{_ZYSQ_PREFIX}/sqStatus", params={"id": record_id}
    )


async def zysq_status_no(record_id: str) -> Any:
    """作业申请驳回"""
    return await api_client.get(
        f"{_ZYSQ_PREFIX}/sqStatusNo", params={"id": record_id}
    )
