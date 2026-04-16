"""全局配置"""

from __future__ import annotations

import os


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class AppConfig:
    """应用配置，host 由登录配置页动态设置"""

    host: str = ""  # 格式: http://ip:port

    # API 前缀
    API_PREFIX: str = "/jeecg-boot/"

    # 上传接口
    UPLOAD_PATH: str = "/jeecg-boot/sys/common/upload"

    # 静态资源路径
    STATIC_PATH: str = "/jeecg-boot/sys/common/static/"

    # 字典接口
    DICT_PATH: str = "/jeecg-boot/sys/dict/getDictItems/"

    # SSL 校验开关：默认关闭（内网自签名），可通过环境变量启用严格校验
    ssl_verify: bool = _env_bool("SCY_SSL_VERIFY", False)

    # 单次请求超时（秒）
    request_timeout: int = int(os.environ.get("SCY_REQUEST_TIMEOUT", "30"))


# 全局单例
app_config = AppConfig()
