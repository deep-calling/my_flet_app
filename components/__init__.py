"""通用组件统一导出"""

from components.status_badge import status_badge, STATUS_COLORS
from components.form_fields import (
    form_item,
    text_field,
    dropdown_field,
    radio_field,
    date_field,
    textarea_field,
    readonly_field,
)
from components.list_page import build_list_page
from components.detail_page import build_detail_page, detail_section
from components.image_upload import ImageUpload
from components.sign_pad import SignPad

__all__ = [
    "status_badge",
    "STATUS_COLORS",
    "form_item",
    "text_field",
    "dropdown_field",
    "radio_field",
    "date_field",
    "textarea_field",
    "readonly_field",
    "build_list_page",
    "build_detail_page",
    "detail_section",
    "ImageUpload",
    "SignPad",
]
