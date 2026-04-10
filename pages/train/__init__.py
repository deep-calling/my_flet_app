"""培训考试模块"""

from pages.train.offline_train import build_offline_train_view, build_offline_train_detail_view
from pages.train.online_learn import build_online_learn_view, build_learn_detail_view, build_training_task_view
from pages.train.online_learn_new import build_online_learn_new_view, build_learn_detail_new_view
from pages.train.brush import build_brush_view
from pages.train.test_list import build_test_view
from pages.train.exam import build_exam_view
from pages.train.results import build_results_view
from pages.train.exam_details import build_exam_details_view, build_exam_info_view

__all__ = [
    "build_offline_train_view",
    "build_offline_train_detail_view",
    "build_online_learn_view",
    "build_learn_detail_view",
    "build_training_task_view",
    "build_online_learn_new_view",
    "build_learn_detail_new_view",
    "build_brush_view",
    "build_test_view",
    "build_exam_view",
    "build_results_view",
    "build_exam_details_view",
    "build_exam_info_view",
]
