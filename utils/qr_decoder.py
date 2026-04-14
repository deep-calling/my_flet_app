"""二维码图片解码工具 — 基于 OpenCV QRCodeDetector"""

from __future__ import annotations


def decode_qr_image(file_path: str) -> str | None:
    """从图片文件解码二维码内容，失败返回 None"""
    try:
        import cv2  # type: ignore
    except ImportError:
        return None

    img = cv2.imread(file_path)
    if img is None:
        return None

    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img)
    if data:
        return data

    # 多码兜底
    try:
        ok, datas, _, _ = detector.detectAndDecodeMulti(img)
        if ok and datas:
            for d in datas:
                if d:
                    return d
    except Exception:
        pass
    return None
