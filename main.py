"""SCY 安全生产信息化管理平台 — Flet 版入口"""

import flet as ft
from urllib.parse import parse_qs

from config import app_config
from pages.login import build_login_view
from pages.login_set import build_login_set_view
from pages.home import build_home_content
from pages.workbench import build_workbench_content
from pages.my import build_my_content
from utils.app_state import app_state
from services.api_client import api_client

# 不需要登录的白名单路由
_AUTH_WHITELIST = {"/login", "/login_set"}


async def main(page: ft.Page):
    try:
        await _main_inner(page)
    except Exception as ex:
        import traceback
        page.controls.clear()
        page.controls.append(
            ft.Column(
                [
                    ft.Text("启动异常", size=20, color=ft.colors.RED),
                    ft.Text(str(ex), selectable=True),
                    ft.Text(traceback.format_exc(), selectable=True, size=12),
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
        )
        await page.update_async()


async def _main_inner(page: ft.Page):
    page.title = "SCY 安全生产信息化管理平台"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.colors.GREY_100

    # 启动时恢复 host 配置
    try:
        saved_ip = await page.client_storage.get_async("base_ip") or ""
        saved_port = await page.client_storage.get_async("base_port") or ""
    except Exception:
        saved_ip = ""
        saved_port = ""
    if saved_ip:
        host = f"http://{saved_ip}:{saved_port or '80'}"
        app_state.host = host
        app_config.host = host

    # Token 失效时自动跳转登录页
    async def _on_token_expired():
        app_state.token = ""
        app_state.user_info = {}
        _tab_cache.clear()
        await page.go_async("/login")

    api_client.on_logout = _on_token_expired

    # Tab 内容缓存
    _tab_cache: dict[int, ft.Control] = {}

    def invalidate_tab_cache():
        """清除 tab 缓存（登录后或需要刷新时调用）"""
        _tab_cache.clear()

    # 将清缓存方法挂到 app_state 上，方便其他地方调用
    app_state.invalidate_tab_cache = invalidate_tab_cache

    # --- TabBar 主页面框架 ---
    async def build_tabbar_view(selected_index: int = 0) -> ft.View:
        """构建带底部 NavigationBar 的主框架视图（完整加载内容）"""

        # 内容区域容器
        content_area = ft.Container(expand=True)

        # 优先使用缓存
        if selected_index in _tab_cache:
            content_area.content = _tab_cache[selected_index]
        else:
            if selected_index == 0:
                content_area.content = await build_home_content(page)
            elif selected_index == 1:
                content_area.content = await build_workbench_content(page)
            elif selected_index == 2:
                content_area.content = await build_my_content(page)
            _tab_cache[selected_index] = content_area.content

        # 底部导航栏切换
        async def on_nav_change(e):
            idx = e.control.selected_index
            # 重新构建视图
            page.views.clear()
            page.views.append(await build_tabbar_view(idx))
            await page.update_async()

        nav_bar = ft.NavigationBar(
            selected_index=selected_index,
            on_change=on_nav_change,
            bgcolor=ft.colors.WHITE,
            destinations=[
                ft.NavigationDestination(icon=ft.icons.HOME_OUTLINED, selected_icon=ft.icons.HOME, label="首页"),
                ft.NavigationDestination(icon=ft.icons.DASHBOARD_OUTLINED, selected_icon=ft.icons.DASHBOARD, label="工作台"),
                ft.NavigationDestination(icon=ft.icons.PERSON_OUTLINE, selected_icon=ft.icons.PERSON, label="我的"),
            ],
        )

        return ft.View(
            route="/home",
            controls=[content_area],
            navigation_bar=nav_bar,
            padding=0,
            spacing=0,
            bgcolor=ft.colors.GREY_100,
        )

    def _build_placeholder_tabbar_view(selected_index: int = 0) -> ft.View:
        """轻量级 TabBar 占位视图（不加载内容，不发起 API 请求）。
        用于子页面路由栈底部，用户按返回时会触发 view_pop 重新导航到 /home。"""

        nav_bar = ft.NavigationBar(
            selected_index=selected_index,
            bgcolor=ft.colors.WHITE,
            destinations=[
                ft.NavigationDestination(icon=ft.icons.HOME_OUTLINED, selected_icon=ft.icons.HOME, label="首页"),
                ft.NavigationDestination(icon=ft.icons.DASHBOARD_OUTLINED, selected_icon=ft.icons.DASHBOARD, label="工作台"),
                ft.NavigationDestination(icon=ft.icons.PERSON_OUTLINE, selected_icon=ft.icons.PERSON, label="我的"),
            ],
        )

        return ft.View(
            route="/home",
            controls=[ft.Container(expand=True)],
            navigation_bar=nav_bar,
            padding=0,
            spacing=0,
            bgcolor=ft.colors.GREY_100,
        )

    # --- 路由解析辅助 ---
    def _parse_route(raw: str) -> tuple[str, dict[str, str]]:
        """将 '/path?a=1&b=2' 拆分为 ('/path', {'a':'1','b':'2'})"""
        if "?" in raw:
            path, qs = raw.split("?", 1)
            params = dict(parse_qs(qs, keep_blank_values=True))
            # parse_qs 返回 list，取第一个
            return path, {k: v[0] if v else "" for k, v in params.items()}
        return raw, {}

    # 路由变更处理
    async def route_change(e: ft.RouteChangeEvent):
        page.views.clear()

        raw_route = page.route
        route, qparams = _parse_route(raw_route)

        # --- 登录拦截 ---
        if route not in _AUTH_WHITELIST and not app_state.token:
            login_view = await build_login_view(page)
            page.views.append(login_view)
            await page.update_async()
            return

        # 登录页
        if route == "/login":
            login_view = await build_login_view(page)
            page.views.append(login_view)

        # 登录配置页（堆栈在登录页之上）
        elif route == "/login_set":
            login_view = await build_login_view(page)
            page.views.append(login_view)
            login_set_view = await build_login_set_view(page)
            page.views.append(login_set_view)

        # 主页（带 TabBar）
        elif route == "/home":
            page.views.append(await build_tabbar_view(0))

        # ========== 双重预防模块路由 ==========

        # 隐患任务 / 包保任务
        elif route in ("/trouble/tasks", "/troublebbzrz/tasks"):
            from pages.trouble.tasks import build_tasks_view
            mtype = "bbzrz" if "bbzrz" in route else "trouble"
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_tasks_view(page, module_type=mtype))

        elif route in ("/trouble/tasks/detail", "/troublebbzrz/tasks/detail"):
            from pages.trouble.tasks import build_task_detail_view
            mtype = "bbzrz" if "bbzrz" in route else "trouble"
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_task_detail_view(page, rid, module_type=mtype))

        # 检查结论
        elif route in ("/trouble/tasks/check_finish", "/troublebbzrz/tasks/check_finish"):
            from pages.trouble.tasks import build_check_finish_view
            mtype = "bbzrz" if "bbzrz" in route else "trouble"
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_check_finish_view(page, rid, module_type=mtype))

        # 任务中隐患上报
        elif route in ("/trouble/tasks/report", "/troublebbzrz/tasks/report"):
            from pages.trouble.tasks import build_report_view
            mtype = "bbzrz" if "bbzrz" in route else "trouble"
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_report_view(page, rid, module_type=mtype))

        # 检查条目列表
        elif route in ("/trouble/tasks/list", "/troublebbzrz/tasks/list"):
            from pages.trouble.tasks import build_task_item_list_view
            mtype = "bbzrz" if "bbzrz" in route else "trouble"
            rid = qparams.get("recordId", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_task_item_list_view(page, rid, module_type=mtype))

        # 排查记录
        elif route in ("/trouble/record", "/troublebbzrz/record"):
            from pages.trouble.record import build_record_view
            mtype = "bbzrz" if "bbzrz" in route else "trouble"
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_record_view(page, module_type=mtype))

        # 隐患整改列表
        elif route in ("/trouble/rectificat", "/troublebbzrz/rectificat"):
            from pages.trouble.rectificat import build_rectificat_view
            mtype = "bbzrz" if "bbzrz" in route else "trouble"
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_rectificat_view(page, module_type=mtype))

        # 整改详情
        elif route in ("/trouble/rectificat/detail", "/troublebbzrz/rectificat/detail"):
            from pages.trouble.rectificat import build_rectificat_detail_view
            mtype = "bbzrz" if "bbzrz" in route else "trouble"
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_rectificat_detail_view(page, rid, module_type=mtype))

        # 新增整改
        elif route in ("/trouble/rectificat/add", "/troublebbzrz/rectificat/add"):
            from pages.trouble.rectificat import build_rectificat_add_view
            mtype = "bbzrz" if "bbzrz" in route else "trouble"
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_rectificat_add_view(page, module_type=mtype))

        # 整改处理
        elif route in ("/trouble/rectificat/deal_zg", "/troublebbzrz/rectificat/deal_zg"):
            from pages.trouble.rectificat import build_zg_deal_view
            mtype = "bbzrz" if "bbzrz" in route else "trouble"
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_zg_deal_view(page, rid, module_type=mtype))

        # 验收处理
        elif route in ("/trouble/rectificat/deal_ys", "/troublebbzrz/rectificat/deal_ys"):
            from pages.trouble.rectificat import build_ys_deal_view
            mtype = "bbzrz" if "bbzrz" in route else "trouble"
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_ys_deal_view(page, rid, module_type=mtype))

        # 隐患上报
        elif route in ("/trouble/handle", "/troublebbzrz/handle"):
            from pages.trouble.handle import build_handle_view
            mtype = "bbzrz" if "bbzrz" in route else "trouble"
            task_rid = qparams.get("taskRecordId", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_handle_view(page, module_type=mtype, task_record_id=task_rid))

        # 隐患上报详情
        elif route in ("/trouble/handle/detail", "/troublebbzrz/handle/detail"):
            from pages.trouble.handle import build_handle_detail_view
            mtype = "bbzrz" if "bbzrz" in route else "trouble"
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_handle_detail_view(page, rid, module_type=mtype))

        # 风险分析对象
        elif route == "/trouble/risk_analysis_object":
            from pages.trouble.risk import build_risk_object_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_risk_object_view(page))
        elif route == "/trouble/risk_analysis_object/detail":
            from pages.trouble.risk import build_risk_object_detail_view
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_risk_object_detail_view(page, rid))

        # 风险分析单元
        elif route == "/trouble/risk_analysis_unit":
            from pages.trouble.risk import build_risk_unit_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_risk_unit_view(page))
        elif route == "/trouble/risk_analysis_unit/detail":
            from pages.trouble.risk import build_risk_unit_detail_view
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_risk_unit_detail_view(page, rid))

        # 风险分析事件
        elif route == "/trouble/risk_analysis_event":
            from pages.trouble.risk import build_risk_event_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_risk_event_view(page))

        # 风险管控措施
        elif route == "/trouble/risk_manage_measure":
            from pages.trouble.risk import build_risk_measure_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_risk_measure_view(page))
        elif route == "/trouble/risk_manage_measure/detail":
            from pages.trouble.risk import build_risk_measure_detail_view
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_risk_measure_detail_view(page, rid))

        # ========== 安全风险分区分级模块路由 ==========

        # 风险研判（特殊：含 tabs + 新增 + 处理）
        elif route == "/security/read":
            from pages.security.read import build_read_list_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_read_list_view(page))
        elif route == "/security/read/add":
            from pages.security.read import build_read_add_view
            ypdw_val = qparams.get("ypdw", "1")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_read_add_view(page, ypdw=ypdw_val))
        elif route == "/security/read/detail":
            from pages.security.read import build_read_detail_view
            rid = qparams.get("id", "")
            is_disabled = qparams.get("disabled", "0") == "1"
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_read_detail_view(page, rid, disabled=is_disabled))
        elif route == "/security/read/deal":
            from pages.security.read import build_read_deal_view
            import json as _json
            tid = qparams.get("taskId", "")
            trans_list = _json.loads(qparams.get("transitionList", "[]"))
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_read_deal_view(page, tid, trans_list))

        # 应急卡
        elif route == "/security/emergency":
            from pages.security import build_emergency_list_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_emergency_list_view(page))
        elif route == "/security/emergency/detail":
            from pages.security import build_emergency_detail_view
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_emergency_detail_view(page, rid))

        # 应知卡
        elif route == "/security/know":
            from pages.security import build_know_list_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_know_list_view(page))
        elif route == "/security/know/detail":
            from pages.security import build_know_detail_view
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_know_detail_view(page, rid))

        # 承诺卡
        elif route == "/security/commitment":
            from pages.security import build_commitment_list_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_commitment_list_view(page))
        elif route == "/security/commitment/detail":
            from pages.security import build_commitment_detail_view
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_commitment_detail_view(page, rid))

        # 管控清单
        elif route == "/security/controls":
            from pages.security import build_controls_list_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_controls_list_view(page))
        elif route == "/security/controls/detail":
            from pages.security import build_identify_detail_view
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_identify_detail_view(page, rid, source="controls"))

        # 辨识清单
        elif route == "/security/identify":
            from pages.security import build_identify_list_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_identify_list_view(page))
        elif route == "/security/identify/detail":
            from pages.security import build_identify_detail_view
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_identify_detail_view(page, rid, source="identify"))

        # 安全管控方法（中间页 + 详情）
        elif route == "/security/method":
            from pages.security import build_method_view
            rid = qparams.get("id", "")
            method_type = qparams.get("method", "")
            from_val = qparams.get("from", "1")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_method_view(page, rid, method_type, from_val))
        elif route == "/security/method/detail":
            from pages.security import build_method_detail_view
            rid = qparams.get("id", "")
            method_type = qparams.get("method", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_method_detail_view(page, rid, method_type))

        # 风险点台账
        elif route == "/security/risk_point":
            from pages.security import build_risk_point_list_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_risk_point_list_view(page))
        elif route == "/security/risk_point/detail":
            from pages.security import build_risk_point_detail_view
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_risk_point_detail_view(page, rid))

        # 风险分区台账
        elif route == "/security/risk_area":
            from pages.security import build_risk_area_list_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_risk_area_list_view(page))
        elif route == "/security/risk_area/detail":
            from pages.security import build_risk_area_detail_view
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_risk_area_detail_view(page, rid))

        # ========== 电子巡检模块路由 ==========

        # 巡检任务列表
        elif route == "/inspection/tasks":
            from pages.inspection import build_inspection_tasks_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_inspection_tasks_view(page))

        # 巡检任务详情
        elif route == "/inspection/detail":
            from pages.inspection import build_inspection_detail_view
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_inspection_detail_view(page, rid))

        # 巡检检查内容页
        elif route == "/inspection/content":
            from pages.inspection import build_inspection_content_view
            import json as _json_mod
            item_str = qparams.get("item", "{}")
            item_data = _json_mod.loads(item_str)
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_inspection_content_view(page, item_data))

        # ========== 作业票模块路由 ==========

        # 作业票列表
        elif route == "/ticket/list":
            from pages.ticket.ticket_list import build_ticket_list_page
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_ticket_list_page(page))

        # 新增/编辑作业票
        elif route == "/ticket/add":
            from pages.ticket.ticket_add import build_ticket_add_page
            type_val = qparams.get("type", "3")
            sq = qparams.get("sq", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_ticket_add_page(page, type_val, sq_id=sq))

        # 作业票详情（含 6 步流程）
        elif route == "/ticket/detail":
            from pages.ticket.ticket_detail import build_ticket_detail_page
            tid = qparams.get("id", "")
            type_val = qparams.get("type", "3")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_ticket_detail_page(page, tid, type_val))

        # 作业票签名
        elif route == "/ticket/sign":
            from pages.ticket.ticket_sign import build_ticket_sign_page
            sign_mode = qparams.get("mode", "")
            sign_info = qparams.get("info", "")
            type_val = qparams.get("type", "3")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_ticket_sign_page(page, sign_mode, sign_info, type_val))

        # 作业申请
        elif route == "/ticket/apply":
            from pages.ticket.ticket_apply import build_ticket_apply_page
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_ticket_apply_page(page))

        # ========== 培训考试模块路由 ==========

        # 线下培训列表
        elif route == "/train/offline":
            from pages.train import build_offline_train_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_offline_train_view(page))

        # 线下培训详情
        elif route == "/train/offline/detail":
            from pages.train import build_offline_train_detail_view
            tid = qparams.get("id", "")
            sign = qparams.get("sign", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_offline_train_detail_view(page, tid, sign=sign))

        # 学习资料列表
        elif route == "/train/materials":
            from pages.train import build_online_learn_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_online_learn_view(page))

        # 学习详情
        elif route == "/train/learn/detail":
            from pages.train import build_learn_detail_view
            mid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_learn_detail_view(page, mid))

        # 线上培训任务列表
        elif route == "/train/task":
            from pages.train import build_training_task_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_training_task_view(page))

        # 线上培训（新版）列表
        elif route == "/train/online":
            from pages.train import build_online_learn_new_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_online_learn_new_view(page))

        # 新版学习详情
        elif route == "/train/learn_new/detail":
            from pages.train import build_learn_detail_new_view
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_learn_detail_new_view(page, rid))

        # 在线刷题
        elif route == "/train/brush":
            from pages.train import build_brush_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_brush_view(page))

        # 在线考试
        elif route == "/train/test":
            from pages.train import build_test_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_test_view(page))

        # 考试/刷题答题页
        elif route == "/train/exam":
            from pages.train import build_exam_view
            tp_id = qparams.get("id", "")
            am = qparams.get("answerMethod", "1")
            eid = qparams.get("examId", "")
            etype = qparams.get("type", "2")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_exam_view(page, tp_id, am, eid, exam_type=etype))

        # 考试结果
        elif route == "/train/results":
            from pages.train import build_results_view
            eid = qparams.get("examId", "")
            etype = qparams.get("type", "2")
            rid = qparams.get("resultId", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_results_view(page, eid, exam_type=etype, result_id=rid))

        # 考试详情
        elif route == "/train/details":
            from pages.train import build_exam_details_view
            eid = qparams.get("examId", "")
            etype = qparams.get("type", "2")
            rid = qparams.get("resultId", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_exam_details_view(page, eid, exam_type=etype, result_id=rid))

        # 试卷解析
        elif route == "/train/info":
            from pages.train import build_exam_info_view
            eid = qparams.get("examId", "")
            rid = qparams.get("resultId", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_exam_info_view(page, exam_id=eid, result_id=rid))

        # ========== 应急演练模块路由 ==========

        # 演练计划列表
        elif route == "/emergency/plan":
            from pages.emergency.plan_list import build_plan_list_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_plan_list_view(page))

        # 演练计划详情
        elif route == "/emergency/plan_detail":
            from pages.emergency.plan_detail import build_plan_detail_view
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_plan_detail_view(page, rid))

        # 应急队伍列表
        elif route == "/emergency/team":
            from pages.emergency.team_list import build_team_list_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_team_list_view(page))

        # 应急队伍详情
        elif route == "/emergency/team_detail":
            from pages.emergency.team_detail import build_team_detail_view
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_team_detail_view(page, rid))

        # 应急物资列表
        elif route == "/emergency/material":
            from pages.emergency.material_list import build_material_list_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_material_list_view(page))

        # 应急物资详情
        elif route == "/emergency/material_detail":
            from pages.emergency.material_detail import build_material_detail_view
            rid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_material_detail_view(page, rid))

        # ========== 进出记录模块路由 ==========

        # 人员进出记录
        elif route == "/record/people":
            from pages.record.people_record import build_people_record_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_people_record_view(page))

        # 车辆进出记录
        elif route == "/record/car":
            from pages.record.car_record import build_car_record_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_car_record_view(page))

        # ========== 报警处理模块路由 ==========

        # 人员定位报警列表
        elif route == "/alarm/personnel":
            from pages.alarm.personnel_list import build_personnel_alarm_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_personnel_alarm_view(page))

        # 人员定位报警处理
        elif route == "/alarm/personnel_detail":
            from pages.alarm.personnel_detail import build_personnel_detail_view
            aid = qparams.get("alarmId", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_personnel_detail_view(page, aid))

        # 监测报警列表
        elif route == "/alarm/indicators":
            from pages.alarm.indicators_list import build_indicators_alarm_view
            today_val = qparams.get("today", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_indicators_alarm_view(page, today=today_val))

        # 监测报警处理
        elif route == "/alarm/indicators_detail":
            from pages.alarm.indicators_detail import build_indicators_detail_view
            aid = qparams.get("alarmId", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_indicators_detail_view(page, aid))

        # ========== 视频监控模块路由 ==========

        # 摄像头列表
        elif route == "/camera":
            from pages.camera_list import build_camera_list_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_camera_list_view(page))

        # 视频播放详情（TODO）
        elif route == "/camera/detail":
            from pages.camera_detail import build_camera_detail_view
            cid = qparams.get("id", "")
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_camera_detail_view(page, cid))

        # ========== 消息模块路由 ==========

        elif route == "/message":
            from pages.message import build_message_view
            page.views.append(_build_placeholder_tabbar_view(0))
            page.views.append(await build_message_view(page))

        # ========== 我的 — 子页面路由 ==========

        # 修改密码
        elif route == "/my/change_password":
            from pages.my.change_password import build_change_password_view
            page.views.append(_build_placeholder_tabbar_view(2))
            page.views.append(await build_change_password_view(page))

        # 关于我们
        elif route == "/my/about":
            from pages.my.aboutus import build_aboutus_view
            page.views.append(_build_placeholder_tabbar_view(2))
            page.views.append(await build_aboutus_view(page))

        # ========== 兜底：未匹配路由 ==========
        else:
            page.views.append(_build_placeholder_tabbar_view(0))

        await page.update_async()

    # 返回处理
    async def view_pop(e: ft.ViewPopEvent):
        if len(page.views) > 1:
            page.views.pop()
            # 弹出子页面后若只剩占位视图，重新加载主页内容
            if len(page.views) == 1 and page.views[0].route == "/home":
                page.views.clear()
                page.views.append(await build_tabbar_view(0))
            await page.update_async()

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # 初始路由：登录页
    await page.go_async("/login")


ft.app(target=main)
