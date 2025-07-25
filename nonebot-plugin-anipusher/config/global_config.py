class AppConfig:
    """存储应用程序配置参数"""

    def __init__(self):
        self.proxy: str | None = None          # 代理服务器地址
        self.tmdb_authorization: str | None = None  # TMDB API密钥
        self.emby_host: str | None = None      # Emby服务器地址
        self.emby_key: str | None = None       # Emby API密钥


class FeatureFlags:
    """管理功能开关状态"""

    def __init__(self):
        self.emby_enabled: bool = False   # Emby功能开关
        self.tmdb_enabled: bool = False   # TMDB功能开关


class PushTarget:
    """存储工作用户信息"""

    def __init__(self):
        self.GroupPushTarget: dict = {}  # 工作用户
        self.PrivatePushTarget: dict = {}  # 工作用户
    """
    示例：
    GroupPushTarget结构
    key为DatabaseTables.TableName枚举值，value为list，存储工作群组ID
    {
    "Ani_RSS":[],
    "Emby":[]
    }
    PrivatePushTarget结构类似
    """


# 全局单例对象
APPCONFIG = AppConfig()
FUNCTION = FeatureFlags()
PUSHTARGET = PushTarget()
