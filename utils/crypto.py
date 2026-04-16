"""轻量对称加密：用于持久化敏感信息（如记住密码）。

基于 stdlib：PBKDF2 派生密钥 + 流式 HMAC-SHA256 作为 keystream（类 CTR）。
不如 AES 强壮，但可避免 client_storage 明文落盘，足以抵挡扫描式泄漏。
密钥基于 host + 固定盐派生，无 host 时不加密（避免静默丢失数据）。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets

_SALT_PREFIX = b"scy-flet-v1::"
_ITER = 60_000


def _derive_key(material: str) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256",
        material.encode("utf-8"),
        _SALT_PREFIX,
        _ITER,
        dklen=32,
    )


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < length:
        block = hmac.new(key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest()
        out.extend(block)
        counter += 1
    return bytes(out[:length])


def encrypt(plaintext: str, material: str) -> str:
    """返回 base64url 编码的 nonce(12) || ciphertext || mac(16)。"""
    if not plaintext or not material:
        return ""
    key = _derive_key(material)
    nonce = secrets.token_bytes(12)
    data = plaintext.encode("utf-8")
    ct = bytes(a ^ b for a, b in zip(data, _keystream(key, nonce, len(data))))
    mac = hmac.new(key, nonce + ct, hashlib.sha256).digest()[:16]
    return base64.urlsafe_b64encode(nonce + ct + mac).decode("ascii")


def decrypt(blob: str, material: str) -> str:
    """解密失败返回空串（不抛异常）。"""
    if not blob or not material:
        return ""
    try:
        raw = base64.urlsafe_b64decode(blob.encode("ascii"))
        if len(raw) < 12 + 16:
            return ""
        nonce, body, mac = raw[:12], raw[12:-16], raw[-16:]
        key = _derive_key(material)
        expected = hmac.new(key, nonce + body, hashlib.sha256).digest()[:16]
        if not hmac.compare_digest(mac, expected):
            return ""
        pt = bytes(a ^ b for a, b in zip(body, _keystream(key, nonce, len(body))))
        return pt.decode("utf-8")
    except (ValueError, UnicodeDecodeError, TypeError):
        return ""


def secret_material() -> str:
    """密钥素材：优先用环境变量，否则用固定应用标识（非机密场景兜底）。"""
    return os.environ.get("SCY_SECRET_MATERIAL") or "scy-flet-device-local"
