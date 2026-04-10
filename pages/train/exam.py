"""考试答题页 — 最复杂的页面

题目类型：是非(1)、单选(2)、多选(3)
答题模式：自由答题(1)、逐题验证(2)、逐题不验证(3)
含倒计时（仅考试 type=2）
"""

from __future__ import annotations

import asyncio
import copy

import flet as ft

from services import train_service as ts

_TYPE_MAP = {"1": "是非题", "2": "单选题", "3": "多选题"}


async def build_exam_view(
    page: ft.Page,
    test_paper_id: str,
    answer_method: str,
    exam_id: str,
    exam_type: str = "2",
) -> ft.View:
    """考试/刷题答题页

    answer_method: '1'=自由答题, '2'=逐题验证, '3'=逐题不验证
    exam_type: '1'=刷题, '2'=考试
    """

    # --- 状态 ---
    questions: list[dict] = []
    current_idx = [0]
    result_id = [""]
    answer_secs = [0]  # 倒计时总秒
    timer_running = [False]
    disabled = [False]  # 当前题是否已确认答案
    exam_submitted = [False]

    # 用户选择的答案 {index: "A" 或 "A,B"}
    user_answers: dict[int, str] = {}

    # --- 控件 ---
    timer_text = ft.Text("", size=14, color=ft.colors.RED)
    question_title = ft.Text("", size=15, weight=ft.FontWeight.W_500)
    question_type_text = ft.Text("", size=12, color=ft.colors.BLUE)
    question_score_text = ft.Text("", size=12, color=ft.colors.GREY_500)
    question_content = ft.Text("", size=14)
    options_column = ft.Column(spacing=4)
    feedback_text = ft.Text("", size=14, visible=False)
    nav_info = ft.Text("", size=13, color=ft.colors.GREY_500)

    # 按钮
    prev_btn = ft.TextButton("上一题", on_click=lambda e: None, visible=False)
    next_btn = ft.TextButton("下一题", on_click=lambda e: None, visible=False)
    confirm_btn = ft.ElevatedButton("确认", on_click=lambda e: None, visible=True,
                                     bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)
    submit_btn = ft.ElevatedButton("交卷", on_click=lambda e: None, visible=False,
                                    bgcolor=ft.colors.RED, color=ft.colors.WHITE)

    # --- 加载题目 ---
    async def _load_questions():
        try:
            data = await ts.get_exam_items(test_paper_id, exam_id)
            if isinstance(data, dict):
                answer_secs[0] = int(data.get("answerSec", 0))
                result_id[0] = data.get("resultId", "")
                items = data.get("tbEduItemLists", [])
                for item in items:
                    q = dict(item)
                    # 多选题：为每个选项添加 check 状态
                    if str(q.get("txfl")) == "3":
                        for opt in q.get("optionsList", []):
                            opt["check"] = False
                    questions.append(q)
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"加载失败：{ex}"), open=True)
            await page.update_async()

    # --- 倒计时 ---
    async def _countdown():
        while timer_running[0] and answer_secs[0] > 0:
            await asyncio.sleep(1)
            answer_secs[0] -= 1
            mins = answer_secs[0] // 60
            secs = answer_secs[0] % 60
            timer_text.value = f"剩余 {mins:02d}:{secs:02d}"
            try:
                await page.update_async()
            except Exception:
                break
        if answer_secs[0] <= 0 and timer_running[0]:
            timer_running[0] = False
            await _auto_submit()

    async def _auto_submit():
        """时间到自动交卷"""
        page.snack_bar = ft.SnackBar(ft.Text("考试时间到，自动交卷"), open=True)
        await page.update_async()
        await asyncio.sleep(1)
        await _do_submit()

    # --- 渲染当前题目 ---
    def _render_question():
        if not questions:
            return
        idx = current_idx[0]
        q = questions[idx]
        txfl = str(q.get("txfl", ""))
        type_name = _TYPE_MAP.get(txfl, "")

        question_title.value = f"第 {idx + 1} 题 / 共 {len(questions)} 题"
        question_type_text.value = f"[{type_name}]  分值：{q.get('btfz', '')}"
        question_content.value = q.get("stnr", "")
        nav_info.value = f"{idx + 1} / {len(questions)}"

        # 选项
        options_column.controls.clear()
        opts = q.get("optionsList", [])

        if txfl in ("1", "2"):
            # 是非 / 单选 → RadioGroup
            current_answer = user_answers.get(idx, "")

            def _make_radio_change(index):
                async def _on_change(e):
                    user_answers[index] = e.control.value
                return _on_change

            radios = []
            for opt in opts:
                radios.append(
                    ft.Radio(
                        value=opt.get("xx", ""),
                        label=f"{opt.get('xx', '')}. {opt.get('xxnr', '')}",
                    )
                )

            rg = ft.RadioGroup(
                value=current_answer or None,
                on_change=_make_radio_change(idx),
                content=ft.Column(controls=radios, spacing=6),
            )
            options_column.controls.append(rg)

        elif txfl == "3":
            # 多选 → Checkbox
            current_answer = user_answers.get(idx, "")
            selected = set(current_answer.split(",")) if current_answer else set()

            for opt in opts:
                xx = opt.get("xx", "")

                def _make_check_change(index, option_key):
                    async def _on_change(e):
                        curr = set(user_answers.get(index, "").split(",")) if user_answers.get(index) else set()
                        if e.control.value:
                            curr.add(option_key)
                        else:
                            curr.discard(option_key)
                        curr.discard("")
                        user_answers[index] = ",".join(sorted(curr))
                    return _on_change

                options_column.controls.append(
                    ft.Checkbox(
                        label=f"{xx}. {opt.get('xxnr', '')}",
                        value=xx in selected,
                        on_change=_make_check_change(idx, xx),
                    )
                )

        # 反馈文本重置
        feedback_text.visible = False
        feedback_text.value = ""

        # 按钮可见性
        disabled[0] = False
        confirm_btn.visible = True

        # 导航按钮
        if answer_method == "1":
            # 自由答题：prev/next 始终可用
            prev_btn.visible = idx > 0
            next_btn.visible = idx < len(questions) - 1
            submit_btn.visible = True
        else:
            # 逐题模式：next 在确认后才可见
            prev_btn.visible = False
            next_btn.visible = False
            submit_btn.visible = idx == len(questions) - 1

    # --- 确认答案 ---
    async def _on_confirm(e):
        if disabled[0]:
            return
        idx = current_idx[0]
        q = questions[idx]
        answer = user_answers.get(idx, "")
        if not answer:
            page.snack_bar = ft.SnackBar(ft.Text("请选择答案"), open=True)
            await page.update_async()
            return

        disabled[0] = True
        confirm_btn.visible = False

        try:
            params: dict = {
                "questionId": q.get("itemId", ""),
                "examId": exam_id,
                "score": q.get("btfz", ""),
                "choose": answer,
            }
            if exam_type == "1" and result_id[0]:
                params["resultId"] = result_id[0]

            resp = await ts.confirm_answer(params)

            if answer_method == "2" and isinstance(resp, dict):
                # 逐题验证：显示对错
                is_correct = str(resp.get("isCorrect", "")) == "1"
                correct_answer = resp.get("correctAnswer", "")
                if is_correct:
                    feedback_text.value = "回答正确！"
                    feedback_text.color = ft.colors.GREEN
                else:
                    feedback_text.value = f"回答错误，正确答案：{correct_answer}"
                    feedback_text.color = ft.colors.RED
                feedback_text.visible = True

            # 逐题模式：显示下一题按钮
            if answer_method != "1":
                if idx < len(questions) - 1:
                    next_btn.visible = True
                else:
                    submit_btn.visible = True

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"提交失败：{ex}"), open=True)
            disabled[0] = False
            confirm_btn.visible = True

        await page.update_async()

    # --- 导航 ---
    async def _on_prev(e):
        if current_idx[0] > 0:
            current_idx[0] -= 1
            _render_question()
            await page.update_async()

    async def _on_next(e):
        if current_idx[0] < len(questions) - 1:
            current_idx[0] += 1
            _render_question()
            await page.update_async()

    # --- 交卷 ---
    async def _do_submit():
        if exam_submitted[0]:
            return
        exam_submitted[0] = True
        timer_running[0] = False
        try:
            data: dict = {"examId": exam_id}
            if exam_type == "1" and result_id[0]:
                data["resultId"] = result_id[0]
            await ts.submit_exam(data)
            page.snack_bar = ft.SnackBar(ft.Text("交卷成功"), open=True)
            await page.update_async()
            await asyncio.sleep(1)
            rid = result_id[0]
            await page.go_async(
                f"/train/results?examId={exam_id}&type={exam_type}"
                + (f"&resultId={rid}" if rid else "")
            )
        except Exception as ex:
            exam_submitted[0] = False
            page.snack_bar = ft.SnackBar(ft.Text(f"交卷失败：{ex}"), open=True)
            await page.update_async()

    async def _on_submit(e):
        # 确认交卷
        async def _confirm_submit(ev):
            dlg.open = False
            await page.update_async()
            await _do_submit()

        async def _cancel(ev):
            dlg.open = False
            await page.update_async()

        # 统计未答题数
        unanswered = sum(1 for i in range(len(questions)) if i not in user_answers or not user_answers[i])

        dlg = ft.AlertDialog(
            title=ft.Text("确认交卷"),
            content=ft.Text(
                f"共 {len(questions)} 题，已答 {len(questions) - unanswered} 题"
                + (f"，还有 {unanswered} 题未作答" if unanswered else "")
                + "。确认交卷？"
            ),
            actions=[
                ft.TextButton("取消", on_click=_cancel),
                ft.TextButton("确认交卷", on_click=_confirm_submit),
            ],
        )
        page.dialog = dlg
        dlg.open = True
        await page.update_async()

    # 绑定按钮事件
    prev_btn.on_click = _on_prev
    next_btn.on_click = _on_next
    confirm_btn.on_click = _on_confirm
    submit_btn.on_click = _on_submit

    # --- 返回确认 ---
    async def _on_back(e):
        async def _confirm_back(ev):
            dlg.open = False
            timer_running[0] = False
            await page.update_async()
            page.views.pop()
            await page.update_async()

        async def _cancel(ev):
            dlg.open = False
            await page.update_async()

        dlg = ft.AlertDialog(
            title=ft.Text("提示"),
            content=ft.Text("确认退出？退出后答题进度将丢失。"),
            actions=[
                ft.TextButton("取消", on_click=_cancel),
                ft.TextButton("确认退出", on_click=_confirm_back),
            ],
        )
        page.dialog = dlg
        dlg.open = True
        await page.update_async()

    # --- 加载并渲染 ---
    await _load_questions()

    if questions:
        _render_question()

    # 启动倒计时（仅考试模式）
    if exam_type == "2" and answer_secs[0] > 0:
        mins = answer_secs[0] // 60
        secs = answer_secs[0] % 60
        timer_text.value = f"剩余 {mins:02d}:{secs:02d}"
        timer_running[0] = True
        asyncio.create_task(_countdown())

    # --- 组装页面 ---
    # 顶部：题号 + 倒计时
    top_bar = ft.Container(
        content=ft.Row(
            controls=[
                question_title,
                timer_text,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
        bgcolor=ft.colors.WHITE,
        border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200)),
    )

    # 题目区域
    question_area = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(controls=[question_type_text, question_score_text], spacing=16),
                ft.Container(height=8),
                question_content,
                ft.Container(height=12),
                options_column,
                ft.Container(height=8),
                feedback_text,
            ],
            spacing=4,
        ),
        padding=ft.padding.all(16),
        bgcolor=ft.colors.WHITE,
        margin=ft.margin.only(top=8),
        border_radius=8,
    )

    # 底部导航栏
    bottom_bar = ft.Container(
        content=ft.Row(
            controls=[
                prev_btn,
                ft.Container(expand=True),
                nav_info,
                ft.Container(expand=True),
                confirm_btn,
                next_btn,
                submit_btn,
            ],
        ),
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        bgcolor=ft.colors.WHITE,
        border=ft.border.only(top=ft.border.BorderSide(1, ft.colors.GREY_200)),
    )

    scroll_area = ft.ListView(
        controls=[question_area],
        expand=True,
        padding=ft.padding.symmetric(horizontal=8),
    )

    body = ft.Column(
        controls=[top_bar, scroll_area, bottom_bar],
        spacing=0,
        expand=True,
    )

    exam_title = "在线刷题" if exam_type == "1" else "在线考试"

    return ft.View(
        route="/train/exam",
        appbar=ft.AppBar(
            title=ft.Text(exam_title),
            bgcolor=ft.colors.WHITE,
            leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=_on_back),
        ),
        controls=[body],
        padding=0,
        bgcolor=ft.colors.GREY_100,
    )
