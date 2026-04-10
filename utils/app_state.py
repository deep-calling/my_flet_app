"""全局应用状态（替代 Vuex）"""

from __future__ import annotations

import json


class AppState:
    """应用状态单例"""

    def __init__(self):
        self.token: str = ""
        self.user_info: dict = {}
        self.host: str = ""  # 格式: http://ip:port

    async def save_to_storage(self, page) -> None:
        """持久化状态到 client_storage"""
        await page.client_storage.set_async("token", self.token)
        await page.client_storage.set_async("user_info", json.dumps(self.user_info))
        await page.client_storage.set_async("host", self.host)

    async def load_from_storage(self, page) -> None:
        """从 client_storage 恢复状态"""
        self.token = await page.client_storage.get_async("token") or ""
        self.host = await page.client_storage.get_async("host") or ""

        user_info_str = await page.client_storage.get_async("user_info")
        if user_info_str:
            self.user_info = json.loads(user_info_str)
        else:
            self.user_info = {}


# 全局单例
app_state = AppState()
