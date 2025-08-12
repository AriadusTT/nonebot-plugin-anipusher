import asyncio
import json
import shutil
import inspect
import importlib
import nonebot_plugin_localstore as store
from pathlib import Path
from nonebot import logger, get_plugin_config
from pydantic import ValidationError
from .monitor_core.abstract_processor import AbstractDataProcessor
from ..exceptions import AppError
from ..database import DBHealthCheck
from ..external import get_request
from ..config import Config, APPCONFIG, FUNCTION, PUSHTARGET, WORKDIR


class HealthCheck:
    def __init__(self) -> None:
        self.connect_task = None

    @classmethod
    async def create_and_run(cls) -> 'HealthCheck':
        instance = cls()
        await instance.run_checks()
        return instance

    async def run_checks(self) -> bool:
        logger.opt(colors=True).info(
            "<g>HealthCheck</g>：Anipusher自检 <g>Start</g>")
        try:
            # 1 读取nonebot localstore路径到全局路径中
            self._load_localstore_path()
            # 2 读取用户配置文件
            self._load_custom_config()
            # 3 读取推送目标用户文件
            self._load_user_data()
            # 4 复制资源文件
            self._res_transfer()
            logger.opt(colors=True).info(
                "<g>HealthCheck</g>：资源配置：<g>PASS</g>")
            logger.opt(colors=True).info("<g>HealthCheck</g>：配置载入：<g>PASS</g>")
            # 5 创建网络测试任务
            self.connect_task = self._create_network_task()
            # 6 数据库检查
            await DBHealthCheck.create_and_check()
            logger.opt(colors=True).info("<g>HealthCheck</g>：数据库：<g>PASS</g>")
            # 7 动态导入所有数据处理器
            await self._import_subclasses()
            logger.opt(colors=True).info(
                "<g>HealthCheck</g>：处理器加载：<g>PASS</g>")
            # 8 获取网络测试任务结果，并配置功能状态
            task_result = await self._get_tasks_result()  # 7.1 获取网络测试任务结果
            parsed_result = self._parse_task_result(
                task_result)        # 7.2 解析任务结果
            self._set_push_status(parsed_result)        # 7.3 配置功能状态
            logger.opt(colors=True).info(
                "<g>HealthCheck</g>：网络联通性：<g>PASS</g>")
            logger.opt(colors=True).info(
                "<g>HealthCheck</g>：<g>ALL Pass</g> 启动监控器")
            return True
        except Exception as e:
            logger.opt(colors=True).error(
                "<r>HealthCheck</r>：Anipusher<r>自检失败</r>!请检查错误信息，监控器将不会启动")
            logger.opt(colors=True).error(e)
            return False

    # 读取nonebot localstore路径到全局路径中
    def _load_localstore_path(self) -> None:
        WORKDIR.cache_dir = store.get_plugin_cache_dir()
        WORKDIR.config_file = store.get_config_file(
            plugin_name="nonebot-plugin-anipusher", filename="anipusheruser.json")
        WORKDIR.data_file = store.get_data_file(
            plugin_name="nonebot-plugin-anipusher", filename="anipusherdb.db")

    # 读取用户配置文件
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

    # 读取推送目标用户文件
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
            if not isinstance(group_target, dict):
                logger.opt(colors=True).error(
                    "<r>HealthCheck</r>：GroupPushTarget格式错误!请检查user.json")
                PUSHTARGET.GroupPushTarget = {}
            PUSHTARGET.GroupPushTarget = group_target
        if private_target := json_data.get("PrivatePushTarget"):
            if not isinstance(private_target, dict):
                logger.opt(colors=True).error(
                    "<r>HealthCheck</r>：PrivatePushTarget格式错误!请检查user.json")
                PUSHTARGET.PrivatePushTarget = {}
            PUSHTARGET.PrivatePushTarget = private_target

    # 重建用户数据文件
    def _reset_user_data(self) -> None:
        try:
            if not WORKDIR.config_file:
                raise AppError.Exception(
                    AppError.MissingData, "<r>HealthCheck</r>：意外的用户文件变量缺失!")
            if not WORKDIR.config_file.parent.is_dir():
                WORKDIR.config_file.parent.mkdir(parents=True)
            WORKDIR.config_file.write_text(json.dumps(
                {"GroupPushTarget": {}, "PrivatePushTarget": {}}, ensure_ascii=False), encoding="utf-8")
            logger.opt(colors=True).info(
                f"<g>HealthCheck</g>：用户数据文件已重建于{WORKDIR.config_file}")
        except Exception as e:
            raise AppError.Exception(AppError.ConfigIOError, f"重置用户数据失败: {e}")

    # 复制资源文件
    def _res_transfer(self) -> None:
        res_dir = Path(__file__).resolve(
        ).parents[1] / "res"
        if not res_dir.is_dir():
            raise AppError.Exception(AppError.MissingData,
                                     f"资源目录缺失: {res_dir}")
        if not WORKDIR.cache_dir:
            raise AppError.Exception(AppError.MissingData,
                                     "<r>HealthCheck</r>：意外的缓存目录变量缺失!")
        WORKDIR.cache_dir.mkdir(parents=True, exist_ok=True)
        work_res_dir = WORKDIR.cache_dir / "res"
        try:
            if work_res_dir.exists():
                shutil.rmtree(work_res_dir)
            shutil.copytree(res_dir, work_res_dir)
        except Exception as e:
            raise AppError.Exception(AppError.MissingData,
                                     f"资源目录复制失败: {e}")

    # 创建网络测试任务
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
        return tasks

    # 动态导入所有数据处理器
    async def _import_subclasses(self) -> None:
        """
        扫描项目文件夹，动态导入所有模块并查找 AbstractDataProcessor 的子类
        Returns:
            list[type[AbstractDataProcessor]]: 找到的所有子类列表
        Raises:
            AppError: 如果基类无效或导入过程中发生严重错误
        """
        subclasses: list[str] = []
        base_class = AbstractDataProcessor
        # 验证基类
        if not inspect.isclass(base_class):
            raise AppError.Exception(AppError.UnSupportedType, "基类必须是类对象")
        # 获取项目根目录
        processor_dir = Path(__file__).resolve().parent
        if not processor_dir.is_dir():
            raise AppError.Exception(AppError.MissingData,
                                     f"处理器目录缺失: {processor_dir}")
        # 遍历目录中的所有文件
        for file in processor_dir.rglob("*.py"):
            # 跳过不需要的文件
            if file.name == "__init__.py" or file.name.startswith(("test_", "_")):
                continue
            try:
                # 转换为模块导入路径
                rel_path = file.relative_to(processor_dir)
                module_path = '.'.join(rel_path.with_suffix('').parts)
                full_module_path = f"{__package__}.{module_path}"
                # 动态导入模块
                module = importlib.import_module(full_module_path)
                # 检查模块中的类
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, base_class) and obj is not base_class and obj.__module__ == module.__name__):
                        subclasses.append(obj.__name__)
            except ImportError as e:
                logger.opt(colors=True).warning(
                    f"<y>HealthCheck</y>：模块导入失败: <r>{file.name}</r> - {str(e)}")
                continue  # 跳过无法导入的模块而不是终止
            except Exception as e:
                logger.opt(colors=True).error(
                    f"<y>HealthCheck</y>：处理模块时出错: <r>{file}</r> - {str(e)}")
                continue  # 记录错误但继续处理其他文件
        logger.opt(colors=True).info(
            f"<g>HealthCheck</g>：处理器导入成功: {subclasses}")

    # 获取网络测试任务结果
    async def _get_tasks_result(self) -> dict:
        # 如果连接检查任务不存在，抛出异常
        if not self.connect_task:
            raise AppError.Exception(AppError.MissingData, "连接检查任务不存在")
        try:
            # 使用asyncio.gather获取所有任务的执行结果
            results = await asyncio.gather(
                *self.connect_task.values(),
                return_exceptions=True
            )  # 获取所有任务的执行结果
            # 返回 {task_name: result} 字典
            return {
                name: res for name, res in zip(self.connect_task.keys(), results)
            }
        except asyncio.CancelledError:
            # 如果任务被取消，抛出异常
            raise AppError.Exception(
                AppError.UnknownError, "<r>HealthCheck</r>：连接检查任务已取消")
        except Exception as e:
            # 如果发生其他异常，抛出异常
            raise AppError.Exception(
                AppError.UnknownError, f"<r>HealthCheck</r>：连接检查任务异常: {e}") from e

    # 解析任务结果
    def _parse_task_result(self, task_result: dict) -> dict:
        parsed = {}
        for task_name, res in task_result.items():
            success = not isinstance(res, Exception)
            parsed[task_name] = {
                "success": success,
                "error": str(res) if not success else None
            }
            if not success:
                logger.opt(colors=True).warning(
                    f"{task_name} failed <y>{type(res).__name__}</y>")
        return parsed

    # 根据网络测试结果，决定是否启用推送功能
    def _set_push_status(self, parsed_result: dict) -> None:
        if not parsed_result:
            raise AppError.Exception(AppError.ParamNotFound, "意外的错误，解析结果为空")
        try:
            # Emby功能开关 (需要ping和info都成功)
            ping_emby_ok = parsed_result.get(
                "ping_emby", {}).get("success", False)
            info_emby_ok = parsed_result.get(
                "info_emby", {}).get("success", False)
            FUNCTION.emby_enabled = ping_emby_ok and info_emby_ok
            logger.opt(colors=True).info(
                f"HealthCheck：Emby功能 {'<g>已启用</g>' if FUNCTION.emby_enabled else '<r>已禁用</r>'}")
        except Exception as e:
            # 全局回退：确保关键功能被禁用
            FUNCTION.emby_enabled = False
            logger.opt(colors=True).error(
                f"<r>HealthCheck</r>：处理 Emby 功能开关时出错，<y>将禁用 Emby 功能</y>: {e}")
        try:
            # TMDB功能开关 (直连或代理任一成功即可)
            tmdb_direct_ok = parsed_result.get(
                "tmdb", {}).get("success", False)
            tmdb_proxy_ok = parsed_result.get(
                "tmdb_with_proxy", {}).get("success", False)
            FUNCTION.tmdb_enabled = tmdb_direct_ok or tmdb_proxy_ok
            # 如果直连成功，则禁用代理
            if tmdb_direct_ok:
                APPCONFIG.proxy = None
            status = (
                "直连 <g>已启用</g>" if tmdb_direct_ok else
                "代理连接 <g>已启用</g>" if tmdb_proxy_ok else
                "<r>已禁用</r>"
            )
            logger.opt(colors=True).info(
                f"HealthCheck：TMDB功能{status}")
        except Exception as e:
            FUNCTION.tmdb_enabled = False
            logger.opt(colors=True).error(
                f"<r>HealthCheck</r>：处理 TMDB 功能开关时出错，<y>将禁用 TMDB 功能</y>: {e}")
