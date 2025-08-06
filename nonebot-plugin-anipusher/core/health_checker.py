import asyncio
from nonebot import logger, get_plugin_config
from pydantic import ValidationError
from ..config import Config, APPCONFIG, FUNCTION, PUSHTARGET, WORKDIR
from ..exceptions import AppError
import json
from ..database import DBHealthCheck
import nonebot_plugin_localstore as store
from ..external import get_request


class HealthCheck:

    @classmethod
    async def create_and_run(cls) -> 'HealthCheck':
        instance = cls()
        await instance.run_checks()
        return instance

    async def run_checks(self) -> None:
        logger.opt(colors=True).info("<g>HealthCheck</g>：Anipusher自检开始")
        # 1 读取nonebot localstore路径到全局路径中
        self._load_localstore_path()
        # 2 读取用户配置文件
        self._load_custom_config()
        # 3 读取推送目标用户文件
        self._load_user_data()
        # 4 创建网络测试任务
        self._create_network_task()

    # 1 读取nonebot localstore路径到全局路径中
    def _load_localstore_path(self) -> None:
        WORKDIR.cache_dir = store.get_plugin_cache_dir()
        WORKDIR.config_file = store.get_config_file(
            plugin_name="nonebot-plugin-anipusher", filename="user.json")
        WORKDIR.data_file = store.get_data_file(
            plugin_name="nonebot-plugin-anipusher", filename="database.db")

    # 2 读取用户配置文件
    def _load_custom_config(self) -> None:
        try:
            self.config = get_plugin_config(Config).anipush
            APPCONFIG.emby_host = self.config.emby_host
            APPCONFIG.emby_key = self.config.emby_apikey
            APPCONFIG.tmdb_authorization = self.config.tmdb_apikey
            APPCONFIG.proxy = self.config.tmdb_proxy
        except ValidationError as e:
            logger.opt(colors=True).error(
                "<r>HealthCheck</r>：配置读取异常!请确认env文件是否已配置")
            logger.opt(colors=True).error(
                "<r>HealthCheck</r>：如果不知道如何填写，请阅读https://github.com/AriadusTT/nonebot-plugin-anipusher/blob/main/README.md")
            logger.opt(colors=True).error(f"<r>HealthCheck</r>：错误信息：{e}")
            raise

    # 3 读取推送目标用户文件
    def _load_user_data(self) -> None:
        if not WORKDIR.config_file:
            raise AppError.Exception(
                AppError.MissingData, "<r>HealthCheck</r>：User文件路径缺失!")
        if not WORKDIR.config_file.is_file():
            # 如果不存在user.json则创建
            self._reset_user_data()
        # 读取推送目标文件
        data = WORKDIR.config_file.read_text(encoding="utf-8")
        json_data = json.loads(data)
        if not json_data:
            raise AppError.Exception(
                AppError.MissingData, "<r>HealthCheck</r>：意外丢失文件数据!")
        if group_target := json_data.get("GroupPushTarget"):
            PUSHTARGET.GroupPushTarget = group_target
        if private_target := json_data.get("PrivatePushTarget"):
            PUSHTARGET.PrivatePushTarget = private_target

    # 3.1 重建用户数据文件
    def _reset_user_data(self) -> None:
        try:
            if not WORKDIR.config_file:
                raise AppError.Exception(
                    AppError.MissingData, "<r>HealthCheck</r>：意外的用户文件变量缺失!")
            if not WORKDIR.config_file.parent.is_dir():
                WORKDIR.config_file.parent.mkdir(parents=True)
            WORKDIR.config_file.write_text(json.dumps(
                {"GroupPushTarget": [], "PrivatePushTarget": []}, ensure_ascii=False), encoding="utf-8")
            logger.opt(colors=True).info(
                f"<g>HealthCheck</g>：用户数据文件已重建于{WORKDIR.config_file}")
        except Exception as e:
            raise AppError.Exception(AppError.ConfigIOError, f"重置用户数据失败: {e}")

    # 4 创建网络测试任务
    def _create_network_task(self) -> dict:
        emby_base = (APPCONFIG.emby_host or "").rstrip("/")
        emby_key = APPCONFIG.emby_key or ""

        ping_emby_url = f"{emby_base}/emby/System/Ping?api_key={emby_key}"
        info_emby_url = f"{emby_base}/emby/System/Info?api_key={emby_key}"

        tmdb_headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {(APPCONFIG.tmdb_authorization or '')}"
        }
        tmdb_api = "https://api.themoviedb.org/3/authentication"
        tasks = {
            "ping_emby": asyncio.create_task(get_request(ping_emby_url)),
            "info_emby": asyncio.create_task(get_request(info_emby_url)),
            "tmdb": asyncio.create_task(get_request(tmdb_api,
                                                    headers=tmdb_headers)),
            "tmdb_with_proxy": asyncio.create_task(get_request(tmdb_api,
                                                               headers=tmdb_headers,
                                                               proxy=APPCONFIG.proxy))
        }
        logger.opt(colors=True).info("HealthCheck：<g>网络测试任务已创建</g>")
        return tasks

    # 5.数据库检查
