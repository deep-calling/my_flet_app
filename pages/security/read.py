"""风险研判与承诺公告 — 含列表(tabs+筛选)、新增/详情表单、审批处理"""

from __future__ import annotations

from typing import Any

import flet as ft

from components.scroll_helper import apply_no_bounce

from services import security_service as ss
from components.form_fields import (
    form_item, text_field, radio_field, dropdown_field, date_field, readonly_field,
)
from components.detail_page import detail_section


# ==================================================================
# 列表页 — 待处理/所有 + 研判单位筛选
# ==================================================================

async def build_read_list_view(page: ft.Page) -> ft.View:
    """风险研判列表页"""

    # --- 状态 ---
    current_tab = [0]  # 0=待处理, 1=所有
    ypdw = ["1"]  # 1=班组, 2=部门/车间, 3=公司
    ypdw_name = ["班组"]
    page_no = [1]
    page_size = 10
    is_bottom = [False]
    items_data: list[dict] = []
    is_loading = [False]

    list_column = ft.Column(spacing=0, expand=True)
    loading_ring = ft.ProgressRing(width=24, height=24, visible=False)
    load_more_btn = ft.Container(visible=False)
    empty_widget = ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(ft.icons.INBOX_OUTLINED, size=64, color=ft.colors.GREY_300),
                ft.Text("暂无数据", size=14, color=ft.colors.GREY_400),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        alignment=ft.alignment.center,
        padding=ft.padding.only(top=120),
        visible=False,
    )

    async def _load_data(reset: bool = False):
        if is_loading[0]:
            return
        is_loading[0] = True
        loading_ring.visible = True
        await page.update_async()

        if reset:
            page_no[0] = 1
            is_bottom[0] = False
            items_data.clear()
            list_column.controls.clear()

        try:
            params: dict[str, Any] = {
                "pageNo": page_no[0],
                "pageSize": page_size,
                "ypdw": ypdw[0],
            }
            # 待处理: bizTaskType=1; 所有: 不传
            if current_tab[0] == 0:
                params["bizTaskType"] = "1"

            result = await ss.announcement_list(params)
            records = result.get("records", []) if isinstance(result, dict) else []
            total = result.get("total", 0) if isinstance(result, dict) else 0

            for item in records:
                items_data.append(item)
                card = _build_item(item)

                def _make_click(data):
                    async def _click(e):
                        disabled = "1" if current_tab[0] == 1 else "0"
                        await page.go_async(
                            f"/security/read/detail?id={data.get('id', '')}&disabled={disabled}"
                        )
                    return _click

                list_column.controls.append(
                    ft.Container(content=card, on_click=_make_click(item), ink=True)
                )

            has_more = len(items_data) < total
            load_more_btn.visible = has_more
            if has_more:
                load_more_btn.content = ft.TextButton(
                    text="加载更多", on_click=_on_load_more,
                    style=ft.ButtonStyle(color=ft.colors.BLUE),
                )
            empty_widget.visible = len(items_data) == 0

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"加载失败：{ex}"), open=True)

        is_loading[0] = False
        loading_ring.visible = False
        await page.update_async()

    async def _on_load_more(e):
        page_no[0] += 1
        await _load_data(reset=False)

    def _build_item(item: dict) -> ft.Control:
        fields = [
            ("公告编号", "id"),
            ("风险级别", "fxjb_dictText"),
            ("承诺日期", "cnrq"),
            ("承诺人", "cnr_dictText"),
            ("有无重大隐患", "ywzdyh_dictText"),
        ]
        rows = [
            ft.Row(
                controls=[
                    ft.Text(f"{label}:", size=13, color=ft.colors.BLACK87, weight=ft.FontWeight.W_500),
                    ft.Text(str(item.get(key, "") or ""), size=13, color=ft.colors.GREY_700, expand=True),
                ],
                spacing=4,
            )
            for label, key in fields
        ]
        return ft.Container(
            content=ft.Column(controls=rows, spacing=6),
            padding=ft.padding.all(14),
            bgcolor=ft.colors.WHITE,
            border_radius=8,
            margin=ft.margin.only(left=12, right=12, top=8),
        )

    # --- Tabs ---
    async def _on_tab_change(e):
        current_tab[0] = e.control.selected_index
        await _load_data(reset=True)

    tabs = ft.Tabs(
        selected_index=0,
        on_change=_on_tab_change,
        tabs=[ft.Tab(text="待处理"), ft.Tab(text="所有")],
        indicator_color=ft.colors.BLUE,
        label_color=ft.colors.BLUE,
        unselected_label_color=ft.colors.GREY_600,
        height=42,
    )

    # --- 研判单位下拉 ---
    ypdw_options = [
        ft.dropdown.Option(key="1", text="班组"),
        ft.dropdown.Option(key="2", text="部门/车间"),
        ft.dropdown.Option(key="3", text="公司"),
    ]

    async def _on_ypdw_change(e):
        ypdw[0] = e.control.value
        for opt in ypdw_options:
            if opt.key == e.control.value:
                ypdw_name[0] = opt.text
                break
        await _load_data(reset=True)

    ypdw_dropdown = ft.Dropdown(
        value="1",
        options=ypdw_options,
        on_change=_on_ypdw_change,
        border_color=ft.colors.GREY_300,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=4),
        text_size=13,
        height=38,
        expand=True,
    )

    filter_bar = ft.Container(
        content=ft.Row(controls=[ypdw_dropdown], spacing=8),
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        bgcolor=ft.colors.WHITE,
    )

    # --- 新增按钮 ---
    async def _on_add(e):
        await page.go_async(f"/security/read/add?ypdw={ypdw[0]}")

    # --- 组装 ---
    scroll_content = ft.ListView(
        controls=[
            list_column,
            ft.Container(
                content=ft.Row(controls=[loading_ring], alignment=ft.MainAxisAlignment.CENTER),
                padding=10,
            ),
            load_more_btn,
            empty_widget,
        ],
        expand=True,
    )
    apply_no_bounce(scroll_content)

    body = ft.Column(
        controls=[tabs, filter_bar, scroll_content],
        spacing=0,
        expand=True,
    )

    view = ft.View(
        route="/security/read",
        appbar=ft.AppBar(
            title=ft.Text("风险研判与承诺公告"),
            bgcolor=ft.colors.WHITE,
            actions=[
                ft.IconButton(ft.icons.ADD, on_click=_on_add, tooltip="新增"),
            ],
        ),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )

    await _load_data(reset=True)
    return view


# ==================================================================
# 新增 / 详情页（共用表单）
# ==================================================================

async def build_read_add_view(page: ft.Page, ypdw: str = "1") -> ft.View:
    """新增风险研判与承诺公告"""

    form_data: dict[str, Any] = {
        "sczz": "", "yxts": "", "tcts": "", "dlzy": "",
        "tsdhzy": "", "yjdhzy": "", "ejdhzy": "", "sxkjzy": "",
        "yjgkzy": "", "ejgczy": "", "sjgczy": "", "lsydzy": "",
        "yjdzzy": "", "ejdzzy": "", "sjdzzy": "", "mbzy": "",
        "jwxzy": "", "dtzy": "",
        "sfycbszy": "", "sfcysscq": "", "sfcyktczt": "", "sfkzzs": "", "ywzdyh": "",
        "fxjb": "", "ypry": "", "ypcl": "", "cnr": "", "cnrq": "",
    }
    display_names: dict[str, str] = {}  # fxjb_name, ypry_name, cnr_name

    # 加载字典
    yes_no_options: list[dict] = []
    level_options: list[dict] = []
    person_options: list[dict] = []

    try:
        yn_result = await ss.get_yes_no_dict()
        if isinstance(yn_result, list):
            yes_no_options = [{"text": i.get("text", ""), "value": str(i.get("value", ""))} for i in yn_result]
    except Exception:
        yes_no_options = [{"text": "是", "value": "1"}, {"text": "否", "value": "0"}]

    try:
        level_result = await ss.get_security_level_dict()
        if isinstance(level_result, list):
            level_options = [{"text": i.get("text", ""), "value": str(i.get("value", ""))} for i in level_result]
    except Exception:
        pass

    try:
        person_result = await ss.get_person_list()
        if isinstance(person_result, dict):
            person_options = [
                {"text": p.get("xm", p.get("realname", "")), "value": p.get("id", "")}
                for p in person_result.get("records", [])
            ]
        elif isinstance(person_result, list):
            person_options = [
                {"text": p.get("xm", p.get("realname", "")), "value": p.get("id", "")}
                for p in person_result
            ]
    except Exception:
        pass

    # 表单字段定义
    number_fields = [
        ("生产装置(套)", "sczz"), ("运行套数(套)", "yxts"), ("停车套数(套)", "tcts"),
        ("断路作业(套)", "dlzy"), ("特殊动火作业(处)", "tsdhzy"), ("一级动火作业(处)", "yjdhzy"),
        ("二级动火作业(处)", "ejdhzy"), ("受限空间作业(处)", "sxkjzy"), ("一级高处作业(处)", "yjgkzy"),
        ("二级高处作业(处)", "ejgczy"), ("三级高处作业(处)", "sjgczy"), ("临时用电作业(处)", "lsydzy"),
        ("一级吊装作业(处)", "yjdzzy"), ("二级吊装作业(处)", "ejdzzy"), ("三级吊装作业(处)", "sjdzzy"),
        ("盲板作业(处)", "mbzy"), ("检维修作业(处)", "jwxzy"), ("动土作业(处)", "dtzy"),
    ]
    radio_fields_cfg = [
        ("是否有承包商作业", "sfycbszy"),
        ("是否处于试生产期", "sfcysscq"),
        ("是否处于开停车状态", "sfcyktczt"),
        ("是否开展中(扩)试", "sfkzzs"),
        ("有无重大隐患", "ywzdyh"),
    ]

    def _make_change(key: str):
        def _on_change(e):
            form_data[key] = e.control.value
        return _on_change

    # 构建表单控件
    form_controls: list[ft.Control] = []

    for label, key in number_fields:
        form_controls.append(text_field(
            label=label, value="", on_change=_make_change(key),
            hint="请填写", keyboard_type=ft.KeyboardType.NUMBER,
        ))

    for label, key in radio_fields_cfg:
        form_controls.append(radio_field(
            label=label, options=yes_no_options, on_change=_make_change(key),
        ))

    # 风险级别
    form_controls.append(dropdown_field(
        label="风险级别", options=level_options,
        on_change=_make_change("fxjb"), hint="请选择",
    ))

    # 研判人员
    form_controls.append(dropdown_field(
        label="研判人员", options=person_options,
        on_change=_make_change("ypry"), hint="请选择",
    ))

    # 承诺人
    form_controls.append(dropdown_field(
        label="承诺人", options=person_options,
        on_change=_make_change("cnr"), hint="请选择",
    ))

    # 承诺日期
    date_text = ft.Text("", size=14)

    async def _on_date_pick(e):
        date_picker = ft.DatePicker(
            first_date=ft.datetime.datetime(2020, 1, 1),
            last_date=ft.datetime.datetime(2050, 12, 31),
        )

        async def _on_date_change(e2):
            if date_picker.value:
                val = date_picker.value.strftime("%Y-%m-%d")
                form_data["cnrq"] = val
                date_text.value = val
                await page.update_async()

        date_picker.on_change = _on_date_change
        page.overlay.append(date_picker)
        await page.update_async()
        date_picker.pick_date()

    form_controls.append(
        ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("承诺日期", size=14, color=ft.colors.GREY_700, width=100),
                    ft.Container(
                        content=ft.Row(controls=[
                            date_text,
                            ft.Icon(ft.icons.CALENDAR_TODAY, size=18, color=ft.colors.GREY_500),
                        ]),
                        expand=True,
                        on_click=_on_date_pick,
                        ink=True,
                        padding=ft.padding.symmetric(vertical=10),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=4),
            bgcolor=ft.colors.WHITE,
        )
    )

    # --- 提交 ---
    async def _on_submit(e):
        try:
            page.snack_bar = ft.SnackBar(ft.Text("提交中..."), open=True)
            await page.update_async()

            submit_data = {**form_data, "ypdw": ypdw}
            result = await ss.add_announcement(submit_data)

            # 发起流程
            if result:
                record_id = result if isinstance(result, str) else str(result)
                await ss.start_process({
                    "flowCode": "dev_tb_security_announcement_001",
                    "id": record_id,
                    "formUrl": "scy/security/announcement/modules/TbSecurityAnnouncementForm",
                })

            page.snack_bar = ft.SnackBar(ft.Text("添加成功"), open=True)
            await page.update_async()

            # 返回
            page.views.pop()
            await page.update_async()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"提交失败：{ex}"), open=True)
            await page.update_async()

    submit_btn = ft.Container(
        content=ft.ElevatedButton(
            text="提交",
            on_click=_on_submit,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE,
            width=200,
        ),
        alignment=ft.alignment.center,
        padding=ft.padding.symmetric(vertical=20),
    )

    # --- 组装 ---
    form_section = ft.Column(
        controls=[
            ft.Container(
                content=ft.Text("基本信息", size=15, weight=ft.FontWeight.W_500),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
            ),
            *form_controls,
            submit_btn,
        ],
        spacing=0,
    )

    return ft.View(
        route="/security/read/add",
        appbar=ft.AppBar(title=ft.Text("新增风险研判与承诺公告"), bgcolor=ft.colors.WHITE),
        controls=[ft.ListView(controls=[form_section], expand=True, padding=0)],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )


# ==================================================================
# 详情页（查看 + 流程步骤 + 处理按钮）
# ==================================================================

async def build_read_detail_view(
    page: ft.Page, record_id: str, disabled: bool = False
) -> ft.View:
    """风险研判详情页 — 只读表单 + 流程步骤 + 处理入口"""

    # 加载详情
    info: dict[str, Any] = {}
    bpm_status = ""
    steps: list[dict] = []
    task_id = ""
    transition_list: list[dict] = []

    try:
        result = await ss.query_announcement_by_id(record_id)
        if isinstance(result, dict):
            records = result.get("records", [])
            info = records[0] if records else {}
            bpm_status = str(info.get("bpmStatus", ""))
    except Exception:
        pass

    # 加载流程步骤
    if record_id and bpm_status != "1":
        try:
            if not disabled:
                node_info = await ss.get_biz_process_node_info({
                    "flowCode": "dev_tb_security_announcement_001",
                    "dataId": record_id,
                })
                if isinstance(node_info, dict):
                    task_id = node_info.get("taskId", "")
                    trans_info = await ss.get_process_task_trans_info({"taskId": task_id})
                    if isinstance(trans_info, dict):
                        transition_list = trans_info.get("transitionList", [])
                        step_list = trans_info.get("bpmLogStepList", [])
                        steps = [{"name": s.get("taskName", "")} for s in step_list]
                        if not steps:
                            steps.append({"name": trans_info.get("taskName", "")})
                        steps.append({"name": "..."})
            else:
                his_info = await ss.get_biz_his_process_node_info({
                    "flowCode": "dev_tb_security_announcement_001",
                    "dataId": record_id,
                })
                if isinstance(his_info, dict):
                    proc_id = his_info.get("procInsId", "")
                    his_trans = await ss.get_his_process_task_trans_info({"procInstId": proc_id})
                    if isinstance(his_trans, dict):
                        step_list = his_trans.get("bpmLogStepList", [])
                        steps = [{"name": s.get("taskName", "")} for s in step_list]
        except Exception:
            pass

    # 构建详情内容
    detail_fields = [
        ("生产装置", "sczz"), ("运行套数", "yxts"), ("停车套数", "tcts"),
        ("断路作业", "dlzy"), ("特殊动火作业", "tsdhzy"), ("一级动火作业", "yjdhzy"),
        ("二级动火作业", "ejdhzy"), ("受限空间作业", "sxkjzy"), ("一级高处作业", "yjgkzy"),
        ("二级高处作业", "ejgczy"), ("三级高处作业", "sjgczy"), ("临时用电作业", "lsydzy"),
        ("一级吊装作业", "yjdzzy"), ("二级吊装作业", "ejdzzy"), ("三级吊装作业", "sjdzzy"),
        ("盲板作业", "mbzy"), ("检维修作业", "jwxzy"), ("动土作业", "dtzy"),
        ("是否有承包商作业", "sfycbszy_dictText"), ("是否处于试生产期", "sfcysscq_dictText"),
        ("是否处于开停车状态", "sfcyktczt_dictText"), ("是否开展中(扩)试", "sfkzzs_dictText"),
        ("有无重大隐患", "ywzdyh_dictText"),
        ("风险级别", "fxjb_dictText"), ("研判人员", "ypry_dictText"),
        ("研判材料", "ypcl"), ("承诺人", "cnr_dictText"), ("承诺日期", "cnrq"),
    ]

    content_controls: list[ft.Control] = []

    # 步骤条
    if steps and bpm_status != "1":
        step_chips = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(s["name"], size=12, color=ft.colors.WHITE if i < len(steps) - 1 else ft.colors.GREY_700),
                    bgcolor=ft.colors.BLUE if i < len(steps) - 1 else ft.colors.GREY_200,
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                )
                for i, s in enumerate(steps)
            ],
            spacing=6,
            wrap=True,
        )
        content_controls.append(ft.Container(
            content=step_chips,
            padding=ft.padding.all(12),
            bgcolor=ft.colors.WHITE,
        ))

    # 基本信息
    fields = [readonly_field(label, str(info.get(key, "") or "-")) for label, key in detail_fields]
    content_controls.append(detail_section("基本信息", fields))

    # 处理按钮
    if not disabled and bpm_status == "2" and task_id:
        async def _on_deal(e):
            try:
                # 获取表单视图
                await page.go_async(
                    f"/security/read/deal?taskId={task_id}&transitionList={_serialize_transitions()}"
                )
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"操作失败：{ex}"), open=True)
                await page.update_async()

        def _serialize_transitions() -> str:
            import json
            return json.dumps(transition_list)

        content_controls.append(ft.Container(
            content=ft.ElevatedButton(
                text="处理", on_click=_on_deal,
                bgcolor=ft.colors.BLUE, color=ft.colors.WHITE, width=200,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(vertical=20),
        ))

    return ft.View(
        route="/security/read/detail",
        appbar=ft.AppBar(title=ft.Text("风险研判与承诺公告详情"), bgcolor=ft.colors.WHITE),
        controls=[
            ft.ListView(
                controls=[ft.Column(controls=content_controls, spacing=0)],
                expand=True, padding=0,
            ),
        ],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )


# ==================================================================
# 处理页（审批）
# ==================================================================

async def build_read_deal_view(
    page: ft.Page, task_id: str, transition_list: list[dict]
) -> ft.View:
    """风险研判审批处理页"""

    form_data = {"reason": "", "files": []}

    reason_field = ft.TextField(
        hint_text="请输入处理意见",
        multiline=True,
        min_lines=3,
        max_lines=6,
        border_color=ft.colors.GREY_300,
        focused_border_color=ft.colors.BLUE,
        text_size=14,
        on_change=lambda e: form_data.__setitem__("reason", e.control.value),
    )

    # 按钮区 — 每个 transition 一个按钮
    async def _make_deal_click(transition: dict):
        async def _click(e):
            try:
                page.snack_bar = ft.SnackBar(ft.Text("提交中..."), open=True)
                await page.update_async()

                import json
                await ss.process_complete({
                    "taskId": task_id,
                    "reason": form_data["reason"],
                    "fileList": json.dumps(form_data["files"]),
                    "nextnode": transition.get("nextnode", ""),
                    "processModel": 1,
                })

                page.snack_bar = ft.SnackBar(ft.Text("提交成功"), open=True)
                await page.update_async()

                # 返回两级（回到列表）
                if len(page.views) >= 2:
                    page.views.pop()
                if len(page.views) >= 2:
                    page.views.pop()
                await page.update_async()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"提交失败：{ex}"), open=True)
                await page.update_async()

        return _click

    btn_controls: list[ft.Control] = []
    for trans in transition_list:
        on_click = await _make_deal_click(trans)
        btn_controls.append(
            ft.ElevatedButton(
                text=trans.get("Transition", "提交"),
                on_click=on_click,
                bgcolor=ft.colors.BLUE,
                color=ft.colors.WHITE,
                expand=True,
            )
        )

    btn_bar = ft.Container(
        content=ft.Row(controls=btn_controls, spacing=12),
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
    )

    form_content = ft.Column(
        controls=[
            ft.Container(
                content=ft.Text("风险研判与承诺审核", size=15, weight=ft.FontWeight.W_500),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
            ),
            ft.Container(
                content=ft.Column(controls=[
                    form_item("处理意见", reason_field),
                ], spacing=0),
                bgcolor=ft.colors.WHITE,
            ),
        ],
        spacing=0,
    )

    return ft.View(
        route="/security/read/deal",
        appbar=ft.AppBar(title=ft.Text("风险研判与承诺处理"), bgcolor=ft.colors.WHITE),
        controls=[
            ft.Column(
                controls=[
                    ft.ListView(controls=[form_content], expand=True, padding=0),
                    btn_bar,
                ],
                spacing=0,
                expand=True,
            ),
        ],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )
