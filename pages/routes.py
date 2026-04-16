"""路由表 — 声明式登记每条子路由的页面加载器。

使用方式：main.py 的 route_change 中先查这张表，命中则调用 build(page, qparams)。
未命中再走根路由（login / login_set / home）和兜底逻辑。

参数映射策略:
    - 简单字符串参数 → 直接传入 build()。
    - trouble / troublebbzrz 共用页面 → 以 trouble 为模板，通过 module_type 注入。
    - tab_index: 子页面返回时底部 NavigationBar 应高亮的 tab；默认 0（首页）。
"""

from __future__ import annotations

import json as _json
from dataclasses import dataclass
from typing import Awaitable, Callable

import flet as ft

ViewBuilder = Callable[[ft.Page, dict[str, str], str], Awaitable[ft.View]]


@dataclass
class RouteSpec:
    """单条路由声明。"""
    builder: ViewBuilder
    tab_index: int = 0           # 占位 tabbar 的高亮位置
    aliases: tuple[str, ...] = ()  # 等价路由；会共享 builder


def _trouble_type(route: str) -> str:
    return "bbzrz" if "bbzrz" in route else "trouble"


# --------------------------------------------------------------------
# 以下 builder 均是 async (page, qparams) -> View
# --------------------------------------------------------------------

async def _trouble_tasks(page, q, route):
    from pages.trouble.tasks import build_tasks_view
    return await build_tasks_view(page, module_type=_trouble_type(route))


async def _trouble_tasks_detail(page, q, route):
    from pages.trouble.tasks import build_task_detail_view
    return await build_task_detail_view(page, q.get("id", ""), module_type=_trouble_type(route))


async def _trouble_tasks_check_finish(page, q, route):
    from pages.trouble.tasks import build_check_finish_view
    return await build_check_finish_view(page, q.get("id", ""), module_type=_trouble_type(route))


async def _trouble_tasks_report(page, q, route):
    from pages.trouble.tasks import build_report_view
    return await build_report_view(page, q.get("id", ""), module_type=_trouble_type(route))


async def _trouble_tasks_list(page, q, route):
    from pages.trouble.tasks import build_task_item_list_view
    return await build_task_item_list_view(page, q.get("recordId", ""), module_type=_trouble_type(route))


async def _trouble_record(page, q, route):
    from pages.trouble.record import build_record_view
    return await build_record_view(page, module_type=_trouble_type(route))


async def _trouble_rectificat(page, q, route):
    from pages.trouble.rectificat import build_rectificat_view
    return await build_rectificat_view(page, module_type=_trouble_type(route))


async def _trouble_rectificat_detail(page, q, route):
    from pages.trouble.rectificat import build_rectificat_detail_view
    return await build_rectificat_detail_view(page, q.get("id", ""), module_type=_trouble_type(route))


async def _trouble_rectificat_add(page, q, route):
    from pages.trouble.rectificat import build_rectificat_add_view
    return await build_rectificat_add_view(page, module_type=_trouble_type(route))


async def _trouble_rectificat_zg(page, q, route):
    from pages.trouble.rectificat import build_zg_deal_view
    return await build_zg_deal_view(page, q.get("id", ""), module_type=_trouble_type(route))


async def _trouble_rectificat_ys(page, q, route):
    from pages.trouble.rectificat import build_ys_deal_view
    return await build_ys_deal_view(page, q.get("id", ""), module_type=_trouble_type(route))


async def _trouble_handle(page, q, route):
    from pages.trouble.handle import build_handle_view
    return await build_handle_view(page, module_type=_trouble_type(route),
                                    task_record_id=q.get("taskRecordId", ""))


async def _trouble_handle_detail(page, q, route):
    from pages.trouble.handle import build_handle_detail_view
    return await build_handle_detail_view(page, q.get("id", ""), module_type=_trouble_type(route))


# 以下路由仅有 /trouble 分支（无 bbzrz 镜像）

async def _risk_object(page, q, route):
    from pages.trouble.risk import build_risk_object_view
    return await build_risk_object_view(page)


async def _risk_object_detail(page, q, route):
    from pages.trouble.risk import build_risk_object_detail_view
    return await build_risk_object_detail_view(page, q.get("id", ""))


async def _risk_unit(page, q, route):
    from pages.trouble.risk import build_risk_unit_view
    return await build_risk_unit_view(page)


async def _risk_unit_detail(page, q, route):
    from pages.trouble.risk import build_risk_unit_detail_view
    return await build_risk_unit_detail_view(page, q.get("id", ""))


async def _risk_event(page, q, route):
    from pages.trouble.risk import build_risk_event_view
    return await build_risk_event_view(page)


async def _risk_measure(page, q, route):
    from pages.trouble.risk import build_risk_measure_view
    return await build_risk_measure_view(page)


async def _risk_measure_detail(page, q, route):
    from pages.trouble.risk import build_risk_measure_detail_view
    return await build_risk_measure_detail_view(page, q.get("id", ""))


# --- 安全风险分区分级 ---

async def _security_read_list(page, q, route):
    from pages.security.read import build_read_list_view
    return await build_read_list_view(page)


async def _security_read_add(page, q, route):
    from pages.security.read import build_read_add_view
    return await build_read_add_view(page, ypdw=q.get("ypdw", "1"))


async def _security_read_detail(page, q, route):
    from pages.security.read import build_read_detail_view
    return await build_read_detail_view(page, q.get("id", ""),
                                         disabled=(q.get("disabled", "0") == "1"))


async def _security_read_deal(page, q, route):
    from pages.security.read import build_read_deal_view
    trans_list = _json.loads(q.get("transitionList", "[]"))
    return await build_read_deal_view(page, q.get("taskId", ""), trans_list)


async def _security_emergency_list(page, q, route):
    from pages.security import build_emergency_list_view
    return await build_emergency_list_view(page)


async def _security_emergency_detail(page, q, route):
    from pages.security import build_emergency_detail_view
    return await build_emergency_detail_view(page, q.get("id", ""))


async def _security_know_list(page, q, route):
    from pages.security import build_know_list_view
    return await build_know_list_view(page)


async def _security_know_detail(page, q, route):
    from pages.security import build_know_detail_view
    return await build_know_detail_view(page, q.get("id", ""))


async def _security_commitment_list(page, q, route):
    from pages.security import build_commitment_list_view
    return await build_commitment_list_view(page)


async def _security_commitment_detail(page, q, route):
    from pages.security import build_commitment_detail_view
    return await build_commitment_detail_view(page, q.get("id", ""))


async def _security_controls_list(page, q, route):
    from pages.security import build_controls_list_view
    return await build_controls_list_view(page)


async def _security_controls_detail(page, q, route):
    from pages.security import build_identify_detail_view
    return await build_identify_detail_view(page, q.get("id", ""), source="controls")


async def _security_identify_list(page, q, route):
    from pages.security import build_identify_list_view
    return await build_identify_list_view(page)


async def _security_identify_detail(page, q, route):
    from pages.security import build_identify_detail_view
    return await build_identify_detail_view(page, q.get("id", ""), source="identify")


async def _security_method(page, q, route):
    from pages.security import build_method_view
    return await build_method_view(page, q.get("id", ""), q.get("method", ""), q.get("from", "1"))


async def _security_method_detail(page, q, route):
    from pages.security import build_method_detail_view
    return await build_method_detail_view(page, q.get("id", ""), q.get("method", ""))


async def _security_risk_point_list(page, q, route):
    from pages.security import build_risk_point_list_view
    return await build_risk_point_list_view(page)


async def _security_risk_point_detail(page, q, route):
    from pages.security import build_risk_point_detail_view
    return await build_risk_point_detail_view(page, q.get("id", ""))


async def _security_risk_area_list(page, q, route):
    from pages.security import build_risk_area_list_view
    return await build_risk_area_list_view(page)


async def _security_risk_area_detail(page, q, route):
    from pages.security import build_risk_area_detail_view
    return await build_risk_area_detail_view(page, q.get("id", ""))


# --- 电子巡检 ---

async def _inspection_tasks(page, q, route):
    from pages.inspection import build_inspection_tasks_view
    return await build_inspection_tasks_view(page)


async def _inspection_detail(page, q, route):
    from pages.inspection import build_inspection_detail_view
    return await build_inspection_detail_view(page, q.get("id", ""))


async def _inspection_content(page, q, route):
    from pages.inspection import build_inspection_content_view
    item_data = _json.loads(q.get("item", "{}"))
    return await build_inspection_content_view(page, item_data)


# --- 作业票 ---

async def _ticket_list(page, q, route):
    from pages.ticket.ticket_list import build_ticket_list_page
    return await build_ticket_list_page(page)


async def _ticket_add(page, q, route):
    from pages.ticket.ticket_add import build_ticket_add_page
    return await build_ticket_add_page(page, q.get("type", "3"), sq_id=q.get("sq", ""))


async def _ticket_detail(page, q, route):
    from pages.ticket.ticket_detail import build_ticket_detail_page
    return await build_ticket_detail_page(page, q.get("id", ""), q.get("type", "3"))


async def _ticket_sign(page, q, route):
    from pages.ticket.ticket_sign import build_ticket_sign_page
    return await build_ticket_sign_page(page, q.get("mode", ""), q.get("info", ""), q.get("type", "3"))


async def _ticket_apply(page, q, route):
    from pages.ticket.ticket_apply import build_ticket_apply_page
    return await build_ticket_apply_page(page)


# --- 培训考试 ---

async def _train_offline(page, q, route):
    from pages.train import build_offline_train_view
    return await build_offline_train_view(page)


async def _train_offline_detail(page, q, route):
    from pages.train import build_offline_train_detail_view
    return await build_offline_train_detail_view(page, q.get("id", ""), sign=q.get("sign", ""))


async def _train_file_viewer(page, q, route):
    from pages.train.file_viewer import build_file_viewer_view
    return await build_file_viewer_view(
        page,
        file_path=q.get("path", ""),
        title=q.get("title", "资料预览"),
        preview_base=q.get("base", "/preview/onlinePreview"),
    )


async def _train_materials(page, q, route):
    from pages.train import build_online_learn_view
    return await build_online_learn_view(page)


async def _train_learn_detail(page, q, route):
    from pages.train import build_learn_detail_view
    return await build_learn_detail_view(page, q.get("id", ""))


async def _train_task(page, q, route):
    from pages.train import build_training_task_view
    return await build_training_task_view(page)


async def _train_online(page, q, route):
    from pages.train import build_online_learn_new_view
    return await build_online_learn_new_view(page)


async def _train_learn_new_detail(page, q, route):
    from pages.train import build_learn_detail_new_view
    return await build_learn_detail_new_view(page, q.get("id", ""))


async def _train_brush(page, q, route):
    from pages.train import build_brush_view
    return await build_brush_view(page)


async def _train_test(page, q, route):
    from pages.train import build_test_view
    return await build_test_view(page)


async def _train_exam(page, q, route):
    from pages.train import build_exam_view
    return await build_exam_view(
        page, q.get("id", ""), q.get("answerMethod", "1"),
        q.get("examId", ""), exam_type=q.get("type", "2"),
    )


async def _train_results(page, q, route):
    from pages.train import build_results_view
    return await build_results_view(
        page, q.get("examId", ""),
        exam_type=q.get("type", "2"),
        result_id=q.get("resultId", ""),
    )


async def _train_details(page, q, route):
    from pages.train import build_exam_details_view
    return await build_exam_details_view(
        page, q.get("examId", ""),
        exam_type=q.get("type", "2"),
        result_id=q.get("resultId", ""),
    )


async def _train_info(page, q, route):
    from pages.train import build_exam_info_view
    return await build_exam_info_view(
        page, exam_id=q.get("examId", ""), result_id=q.get("resultId", ""),
    )


# --- 应急演练 ---

async def _emergency_plan(page, q, route):
    from pages.emergency.plan_list import build_plan_list_view
    return await build_plan_list_view(page)


async def _emergency_plan_detail(page, q, route):
    from pages.emergency.plan_detail import build_plan_detail_view
    return await build_plan_detail_view(page, q.get("id", ""))


async def _emergency_team(page, q, route):
    from pages.emergency.team_list import build_team_list_view
    return await build_team_list_view(page)


async def _emergency_team_detail(page, q, route):
    from pages.emergency.team_detail import build_team_detail_view
    return await build_team_detail_view(page, q.get("id", ""))


async def _emergency_material(page, q, route):
    from pages.emergency.material_list import build_material_list_view
    return await build_material_list_view(page)


async def _emergency_material_detail(page, q, route):
    from pages.emergency.material_detail import build_material_detail_view
    return await build_material_detail_view(page, q.get("id", ""))


# --- 进出记录 ---

async def _record_people(page, q, route):
    from pages.record.people_record import build_people_record_view
    return await build_people_record_view(page)


async def _record_car(page, q, route):
    from pages.record.car_record import build_car_record_view
    return await build_car_record_view(page)


# --- 报警处理 ---

async def _alarm_personnel(page, q, route):
    from pages.alarm.personnel_list import build_personnel_alarm_view
    return await build_personnel_alarm_view(page)


async def _alarm_personnel_detail(page, q, route):
    from pages.alarm.personnel_detail import build_personnel_detail_view
    return await build_personnel_detail_view(page, q.get("alarmId", ""))


async def _alarm_indicators(page, q, route):
    from pages.alarm.indicators_list import build_indicators_alarm_view
    return await build_indicators_alarm_view(page, today=q.get("today", ""))


async def _alarm_indicators_detail(page, q, route):
    from pages.alarm.indicators_detail import build_indicators_detail_view
    return await build_indicators_detail_view(page, q.get("alarmId", ""))


# --- 视频监控 ---

async def _camera_list(page, q, route):
    from pages.camera_list import build_camera_list_view
    return await build_camera_list_view(page)


async def _camera_detail(page, q, route):
    from pages.camera_detail import build_camera_detail_view
    return await build_camera_detail_view(page, q.get("id", ""))


# --- 消息 ---

async def _message(page, q, route):
    from pages.message import build_message_view
    return await build_message_view(page)


# --- 我的 ---

async def _my_change_password(page, q, route):
    from pages.my.change_password import build_change_password_view
    return await build_change_password_view(page)


async def _my_about(page, q, route):
    from pages.my.aboutus import build_aboutus_view
    return await build_aboutus_view(page)


ROUTES: dict[str, RouteSpec] = {
    # ---- 双重预防（trouble / bbzrz 共用） ----
    "/trouble/tasks":              RouteSpec(_trouble_tasks, aliases=("/troublebbzrz/tasks",)),
    "/trouble/tasks/detail":       RouteSpec(_trouble_tasks_detail, aliases=("/troublebbzrz/tasks/detail",)),
    "/trouble/tasks/check_finish": RouteSpec(_trouble_tasks_check_finish, aliases=("/troublebbzrz/tasks/check_finish",)),
    "/trouble/tasks/report":       RouteSpec(_trouble_tasks_report, aliases=("/troublebbzrz/tasks/report",)),
    "/trouble/tasks/list":         RouteSpec(_trouble_tasks_list, aliases=("/troublebbzrz/tasks/list",)),
    "/trouble/record":             RouteSpec(_trouble_record, aliases=("/troublebbzrz/record",)),
    "/trouble/rectificat":         RouteSpec(_trouble_rectificat, aliases=("/troublebbzrz/rectificat",)),
    "/trouble/rectificat/detail":  RouteSpec(_trouble_rectificat_detail, aliases=("/troublebbzrz/rectificat/detail",)),
    "/trouble/rectificat/add":     RouteSpec(_trouble_rectificat_add, aliases=("/troublebbzrz/rectificat/add",)),
    "/trouble/rectificat/deal_zg": RouteSpec(_trouble_rectificat_zg, aliases=("/troublebbzrz/rectificat/deal_zg",)),
    "/trouble/rectificat/deal_ys": RouteSpec(_trouble_rectificat_ys, aliases=("/troublebbzrz/rectificat/deal_ys",)),
    "/trouble/handle":             RouteSpec(_trouble_handle, aliases=("/troublebbzrz/handle",)),
    "/trouble/handle/detail":      RouteSpec(_trouble_handle_detail, aliases=("/troublebbzrz/handle/detail",)),

    # ---- 风险分析 ----
    "/trouble/risk_analysis_object":          RouteSpec(_risk_object),
    "/trouble/risk_analysis_object/detail":   RouteSpec(_risk_object_detail),
    "/trouble/risk_analysis_unit":            RouteSpec(_risk_unit),
    "/trouble/risk_analysis_unit/detail":     RouteSpec(_risk_unit_detail),
    "/trouble/risk_analysis_event":           RouteSpec(_risk_event),
    "/trouble/risk_manage_measure":           RouteSpec(_risk_measure),
    "/trouble/risk_manage_measure/detail":    RouteSpec(_risk_measure_detail),

    # ---- 安全风险分区分级 ----
    "/security/read":              RouteSpec(_security_read_list),
    "/security/read/add":          RouteSpec(_security_read_add),
    "/security/read/detail":       RouteSpec(_security_read_detail),
    "/security/read/deal":         RouteSpec(_security_read_deal),
    "/security/emergency":         RouteSpec(_security_emergency_list),
    "/security/emergency/detail":  RouteSpec(_security_emergency_detail),
    "/security/know":              RouteSpec(_security_know_list),
    "/security/know/detail":       RouteSpec(_security_know_detail),
    "/security/commitment":        RouteSpec(_security_commitment_list),
    "/security/commitment/detail": RouteSpec(_security_commitment_detail),
    "/security/controls":          RouteSpec(_security_controls_list),
    "/security/controls/detail":   RouteSpec(_security_controls_detail),
    "/security/identify":          RouteSpec(_security_identify_list),
    "/security/identify/detail":   RouteSpec(_security_identify_detail),
    "/security/method":            RouteSpec(_security_method),
    "/security/method/detail":     RouteSpec(_security_method_detail),
    "/security/risk_point":        RouteSpec(_security_risk_point_list),
    "/security/risk_point/detail": RouteSpec(_security_risk_point_detail),
    "/security/risk_area":         RouteSpec(_security_risk_area_list),
    "/security/risk_area/detail":  RouteSpec(_security_risk_area_detail),

    # ---- 电子巡检 ----
    "/inspection/tasks":  RouteSpec(_inspection_tasks),
    "/inspection/detail": RouteSpec(_inspection_detail),
    "/inspection/content": RouteSpec(_inspection_content),

    # ---- 作业票 ----
    "/ticket/list":    RouteSpec(_ticket_list),
    "/ticket/add":     RouteSpec(_ticket_add),
    "/ticket/detail":  RouteSpec(_ticket_detail),
    "/ticket/sign":    RouteSpec(_ticket_sign),
    "/ticket/apply":   RouteSpec(_ticket_apply),

    # ---- 培训考试 ----
    "/train/offline":         RouteSpec(_train_offline),
    "/train/offline/detail":  RouteSpec(_train_offline_detail),
    "/train/file_viewer":     RouteSpec(_train_file_viewer),
    "/train/materials":       RouteSpec(_train_materials),
    "/train/learn/detail":    RouteSpec(_train_learn_detail),
    "/train/task":            RouteSpec(_train_task),
    "/train/online":          RouteSpec(_train_online),
    "/train/learn_new/detail": RouteSpec(_train_learn_new_detail),
    "/train/brush":           RouteSpec(_train_brush),
    "/train/test":            RouteSpec(_train_test),
    "/train/exam":            RouteSpec(_train_exam),
    "/train/results":         RouteSpec(_train_results),
    "/train/details":         RouteSpec(_train_details),
    "/train/info":            RouteSpec(_train_info),

    # ---- 应急演练 ----
    "/emergency/plan":            RouteSpec(_emergency_plan),
    "/emergency/plan_detail":     RouteSpec(_emergency_plan_detail),
    "/emergency/team":            RouteSpec(_emergency_team),
    "/emergency/team_detail":     RouteSpec(_emergency_team_detail),
    "/emergency/material":        RouteSpec(_emergency_material),
    "/emergency/material_detail": RouteSpec(_emergency_material_detail),

    # ---- 进出记录 ----
    "/record/people": RouteSpec(_record_people),
    "/record/car":    RouteSpec(_record_car),

    # ---- 报警处理 ----
    "/alarm/personnel":          RouteSpec(_alarm_personnel),
    "/alarm/personnel_detail":   RouteSpec(_alarm_personnel_detail),
    "/alarm/indicators":         RouteSpec(_alarm_indicators),
    "/alarm/indicators_detail":  RouteSpec(_alarm_indicators_detail),

    # ---- 视频监控 ----
    "/camera":        RouteSpec(_camera_list),
    "/camera/detail": RouteSpec(_camera_detail),

    # ---- 消息 ----
    "/message": RouteSpec(_message),

    # ---- 我的 ----
    "/my/change_password": RouteSpec(_my_change_password, tab_index=2),
    "/my/about":           RouteSpec(_my_about, tab_index=2),
}


def resolve(route: str) -> RouteSpec | None:
    """按 route 精确查表；同时解析 aliases。"""
    spec = ROUTES.get(route)
    if spec is not None:
        return spec
    for primary, s in ROUTES.items():
        if route in s.aliases:
            return s
    return None
