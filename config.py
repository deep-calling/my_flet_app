"""全局配置"""


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


# 全局单例
app_config = AppConfig()
