"""基于标准库 urllib 的 API 客户端封装（兼容 Android）"""

from __future__ import annotations

import asyncio
import json as _json
import ssl
import urllib.request
import urllib.error
import urllib.parse
from typing import Any
from uuid import uuid4

from config import app_config
from utils.app_state import app_state

# 忽略 SSL 验证（Android 上证书链可能不全）
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


class ApiClient:
    """HTTP 客户端，自动注入 Token、拦截响应"""

    def __init__(self):
        # 登出回调，由外部注入（如 main.py 中设置跳转登录页）
        self.on_logout: Any = None
        self.timeout: int = 30

    @property
    def base_url(self) -> str:
        return app_config.host

    def _get_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if app_state.token:
            headers["X-Access-Token"] = app_state.token
        return headers

    def _do_request(self, url: str, data: bytes | None = None,
                    headers: dict | None = None, method: str = "GET") -> Any:
        """同步执行 HTTP 请求（在线程中调用）"""
        req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
        with urllib.request.urlopen(req, timeout=self.timeout, context=_ssl_ctx) as resp:
            return _json.loads(resp.read().decode("utf-8"))

    async def _handle_response(self, data: dict) -> Any:
        """统一响应处理：成功返回 data，Token 失效触发登出"""
        code = data.get("code", -1)

        # Token 失效检测
        if code == 500 and "Token失效" in data.get("message", ""):
            app_state.token = ""
            if self.on_logout:
                await self.on_logout()
            raise PermissionError("Token失效，请重新登录")

        # 正常响应
        if code in (200, 0):
            return data.get("result", data.get("data"))

        # 其他错误
        raise Exception(data.get("message", "请求失败"))

    async def get(self, path: str, params: dict | None = None) -> Any:
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        headers = self._get_headers()
        raw = await asyncio.to_thread(self._do_request, url, None, headers, "GET")
        return await self._handle_response(raw)

    async def post(self, path: str, json: dict | None = None) -> Any:
        url = f"{self.base_url}{path}"
        headers = self._get_headers()
        body = _json.dumps(json or {}).encode("utf-8")
        raw = await asyncio.to_thread(self._do_request, url, body, headers, "POST")
        return await self._handle_response(raw)

    async def put(self, path: str, json: dict | None = None) -> Any:
        url = f"{self.base_url}{path}"
        headers = self._get_headers()
        body = _json.dumps(json or {}).encode("utf-8")
        raw = await asyncio.to_thread(self._do_request, url, body, headers, "PUT")
        return await self._handle_response(raw)

    async def delete(self, path: str, params: dict | None = None) -> Any:
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        headers = self._get_headers()
        raw = await asyncio.to_thread(self._do_request, url, None, headers, "DELETE")
        return await self._handle_response(raw)

    async def upload(self, path: str, file_path: str, field_name: str = "file") -> str:
        """上传文件（multipart/form-data），返回服务器相对路径"""
        import os
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            file_data = f.read()
        return await self.upload_bytes(path, file_data, filename, field_name)

    async def upload_bytes(
        self,
        path: str,
        file_data: bytes,
        filename: str = "upload.png",
        field_name: str = "file",
        content_type: str = "application/octet-stream",
    ) -> str:
        """直接上传字节内容（multipart/form-data），返回服务器相对路径。

        JeecgBoot 上传接口响应格式：
        { "success": true, "message": "<relative/path>", "code": 200, "result": null }
        文件路径在 message 字段。
        """
        url = f"{self.base_url}{path}"
        boundary = uuid4().hex

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
        if app_state.token:
            headers["X-Access-Token"] = app_state.token

        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

        raw = await asyncio.to_thread(self._do_request, url, body, headers, "POST")
        code = raw.get("code", -1)

        if code == 500 and "Token失效" in str(raw.get("message", "")):
            app_state.token = ""
            if self.on_logout:
                await self.on_logout()
            raise PermissionError("Token失效，请重新登录")

        if raw.get("success") is True or code in (200, 0):
            msg = raw.get("message") or raw.get("result") or ""
            if isinstance(msg, str) and msg:
                return msg
            raise Exception("上传成功但未返回文件路径")

        raise Exception(raw.get("message", "上传失败"))


# 全局单例
api_client = ApiClient()
