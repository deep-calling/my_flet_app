"""基于 httpx.AsyncClient 的 API 客户端（连接池 + 可配 SSL）"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable
from uuid import uuid4

import httpx

from config import app_config
from utils.app_state import app_state
from utils.logger import get_logger

log = get_logger("api")

# 业务层识别为"登录失效"的响应码（除了 code，还要结合 message 关键词）
_TOKEN_EXPIRED_CODES = {401, 510}
_TOKEN_EXPIRED_KEYWORDS = ("Token失效", "token失效", "请登录", "未登录", "token expired")


class TokenExpired(PermissionError):
    """Token 失效异常（业务可捕获）"""


class ApiError(Exception):
    def __init__(self, message: str, code: int = -1, raw: dict | None = None):
        super().__init__(message)
        self.code = code
        self.raw = raw or {}


class ApiClient:
    """HTTP 客户端：连接池 + 自动注入 Token + 统一响应处理"""

    def __init__(self):
        self.on_logout: Callable[[], Awaitable[None]] | None = None
        self._client: httpx.AsyncClient | None = None
        self._client_lock = asyncio.Lock()
        self._current_verify: bool | None = None

    @property
    def base_url(self) -> str:
        return app_config.host

    async def _get_client(self) -> httpx.AsyncClient:
        """懒加载 AsyncClient；SSL 设置变化时重建。"""
        verify = bool(app_config.ssl_verify)
        async with self._client_lock:
            if self._client is None or self._current_verify != verify:
                if self._client is not None:
                    await self._client.aclose()
                self._client = httpx.AsyncClient(
                    verify=verify,
                    timeout=app_config.request_timeout,
                    limits=httpx.Limits(
                        max_keepalive_connections=10,
                        max_connections=20,
                    ),
                    trust_env=False,
                )
                self._current_verify = verify
            return self._client

    async def close(self) -> None:
        async with self._client_lock:
            if self._client is not None:
                await self._client.aclose()
                self._client = None

    def _headers(self, extra: dict | None = None) -> dict:
        headers = {"Content-Type": "application/json"}
        if app_state.token:
            headers["X-Access-Token"] = app_state.token
        if extra:
            headers.update(extra)
        return headers

    def _is_token_expired(self, code: int, message: str) -> bool:
        if code in _TOKEN_EXPIRED_CODES:
            return True
        if code == 500 and message:
            return any(k in message for k in _TOKEN_EXPIRED_KEYWORDS)
        return False

    async def _handle_response(self, data: dict) -> Any:
        if not isinstance(data, dict):
            return data
        code = int(data.get("code", data.get("status", -1)) or -1)
        message = str(data.get("message", "") or "")

        if self._is_token_expired(code, message):
            log.warning("token expired (code=%s, msg=%s)", code, message)
            app_state.token = ""
            if self.on_logout is not None:
                try:
                    await self.on_logout()
                except Exception:
                    log.exception("on_logout handler raised")
            raise TokenExpired("登录已失效，请重新登录")

        if code in (200, 0) or data.get("success") is True:
            return data.get("result", data.get("data"))

        raise ApiError(message or "请求失败", code=code, raw=data)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
        content: bytes | None = None,
        headers: dict | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        client = await self._get_client()
        try:
            resp = await client.request(
                method,
                url,
                params=params,
                json=json,
                content=content,
                headers=self._headers(headers),
            )
            resp.raise_for_status()
            return await self._handle_response(resp.json())
        except httpx.HTTPStatusError as ex:
            log.error("HTTP %s %s -> %s", method, url, ex.response.status_code)
            try:
                payload = ex.response.json()
            except ValueError:
                raise ApiError(f"HTTP {ex.response.status_code}") from ex
            return await self._handle_response(payload)
        except httpx.HTTPError as ex:
            log.exception("request failed: %s %s", method, url)
            raise ApiError(f"网络异常：{ex}") from ex

    async def get(self, path: str, params: dict | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json: dict | None = None) -> Any:
        return await self._request("POST", path, json=json or {})

    async def put(self, path: str, json: dict | None = None) -> Any:
        return await self._request("PUT", path, json=json or {})

    async def delete(self, path: str, params: dict | None = None) -> Any:
        return await self._request("DELETE", path, params=params)

    # ---------- 上传 ----------

    async def upload(self, path: str, file_path: str, field_name: str = "file") -> str:
        """上传本地文件（非阻塞读取）。"""
        import os

        def _read() -> tuple[str, bytes]:
            with open(file_path, "rb") as f:
                return os.path.basename(file_path), f.read()

        filename, data = await asyncio.to_thread(_read)
        return await self.upload_bytes(path, data, filename, field_name)

    async def upload_bytes(
        self,
        path: str,
        file_data: bytes,
        filename: str = "upload.png",
        field_name: str = "file",
        content_type: str = "application/octet-stream",
    ) -> str:
        """返回服务器相对路径（JeecgBoot 约定放在 message 字段）。"""
        url = f"{self.base_url}{path}"
        client = await self._get_client()
        files = {field_name: (filename, file_data, content_type)}

        headers: dict[str, str] = {}
        if app_state.token:
            headers["X-Access-Token"] = app_state.token

        try:
            resp = await client.post(url, files=files, headers=headers)
            resp.raise_for_status()
            raw = resp.json()
        except httpx.HTTPError as ex:
            log.exception("upload failed: %s", url)
            raise ApiError(f"上传失败：{ex}") from ex

        code = int(raw.get("code", -1) or -1)
        message = str(raw.get("message", "") or "")
        if self._is_token_expired(code, message):
            app_state.token = ""
            if self.on_logout is not None:
                try:
                    await self.on_logout()
                except Exception:
                    log.exception("on_logout handler raised")
            raise TokenExpired("登录已失效，请重新登录")

        if raw.get("success") is True or code in (200, 0):
            msg = raw.get("message") or raw.get("result") or ""
            if isinstance(msg, str) and msg:
                return msg
            raise ApiError("上传成功但未返回文件路径", code=code, raw=raw)

        raise ApiError(message or "上传失败", code=code, raw=raw)

    # 兼容以 uuid boundary 手写 multipart 的调用点
    async def upload_raw_multipart(
        self,
        path: str,
        file_data: bytes,
        filename: str,
        field_name: str,
        content_type: str,
    ) -> str:
        return await self.upload_bytes(
            path, file_data, filename, field_name, content_type
        )


# 全局单例
api_client = ApiClient()
