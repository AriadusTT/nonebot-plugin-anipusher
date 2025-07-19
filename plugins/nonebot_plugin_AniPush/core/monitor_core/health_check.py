
import inspect
import importlib
import shutil
import asyncio
from pathlib import Path
from pydantic import ValidationError
from dotenv import dotenv_values, set_key
from nonebot import logger, get_plugin_config
from ...constants.error_handling import AppError
from ...external.requests import get_request
from ...config import JsonIO, Config, AnipushConfig, APPCONFIG, FUNCTION, PUSHTARGET
from ...database.db_health_check import DBHealthCheck
from ...core.monitor_core.abstract_processor import AbstractDataProcessor


# # 已弃用，请使用NewHealthCheck
# class HealthCheck:
#     def __init__(self):
#         self.target_path = Path(
#             __file__).resolve().parents[2] / "target.json"
#         self.complete_process_num = 0
#         self.conntect_task = None

#     @classmethod
#     async def create_and_run(cls) -> 'HealthCheck':
#         instance = cls()
#         await instance.run_checks()
#         return instance

#     async def run_checks(self):
#         logger.opt(colors=True).info("AniPusher：启动自检")
#         # 检查插件配置
#         self._check_and_load_config()
#         # 检查配置文件并载入全局变量
#         # try:
#         #     config_data = await self._load_json()
#         #     self._init_push_target(config_data)
#         #     self.complete_process_num += 1
#         #     logger.opt(colors=True).info(
#         #         f"AniPusher:<g>({self.complete_process_num}/4)配置检查 & 载入 完成</g>")
#         # except (AppError.Exception, Exception) as e:
#         #     logger.opt(colors=True).error(f"AniPusher:<r>(1/3)配置检查失败!</r>:{e}")
#         #     raise
#         # 创建连接检查任务
#         try:
#             self.conntect_task = self._create_task()
#             logger.opt(colors=True).info("AniPusher:<g>网络测试任务已创建</g>，正在后台运行")
#         except Exception as e:
#             raise AppError.Exception(AppError.UnknownError, f"任务创建失败: {e}")
#         # 检查数据库结构
#         try:
#             await self._run_database_checks()
#             self.complete_process_num += 1
#             logger.opt(colors=True).info(
#                 f"AniPusher:<g>({self.complete_process_num}/4)数据库初始化 & 自检 完成</g>")
#         except (AppError.Exception, Exception) as e:
#             logger.opt(colors=True).error(
#                 f"AniPusher:<r>数据库检查失败!</r>:{e}")
#             raise
#         # 加载数据处理器
#         try:
#             subclasses = await self._import_subclasses()
#             self.complete_process_num += 1
#             logger.opt(colors=True).info(
#                 f"AniPusher:<g>({self.complete_process_num}/4)数据处理器扫描 完成</g>，共找到 {len(subclasses)} 个子类")
#         except (AppError.Exception, Exception) as e:
#             logger.opt(colors=True).error(
#                 f"AniPusher:<r>数据处理器加载失败!</r>:{e}")
#             raise
#         # 获取连接任务结果
#         try:
#             task_result = await self._get_tasks_result()
#             self._task_result_process(task_result)
#             self.complete_process_num += 1
#             logger.opt(colors=True).info(
#                 f"AniPusher:<g>({self.complete_process_num}/4)网络检查任务完成，功能开关已配置</g>")
#         except (AppError.Exception, Exception) as e:
#             logger.opt(colors=True).error(
#                 f"AniPusher:<r>任务结果获取失败!</r>:{e}")
#             raise
#         logger.opt(colors=True).info("AniPusher:自检完成")

#     # 分析配置读取结果
#     def _check_and_load_config(self) -> None:
#         try:
#             self.config = get_plugin_config(Config).anipush
#         except ValidationError as e:
#             logger.opt(colors=True).error(
#                 f"AniPusher:<r>确认配置文件缺少必须项!</r>:{e}，将重建配置文件")
#         except Exception as e:
#             raise AppError.Exception(
#                 AppError.UnknownError, f"配置文件读取失败: {e}")
#         # 载入全局变量
#         APPCONFIG.emby_host = self.config.emby_host
#         APPCONFIG.emby_key = self.config.emby_apikey
#         APPCONFIG.tmdb_authorization = self.config.tmdb_apikey
#         APPCONFIG.proxy = self.config.tmdb_proxy

#     # 读取推送对象json文件
#     async def _load_json(self) -> dict:
#         json_data = None  # 初始化
#         if not self.target_path.is_file():
#             logger.opt(colors=True).warning(
#                 "<y>HealthCheck</y>：target.json缺失!将创建默认配置文件")
#             try:
#                 self.__new_target_json()
#             except (AppError.Exception, Exception):
#                 raise
#         try:
#             json_data = JsonIO.read_json(self.target_path)
#         except (AppError.Exception, Exception):
#             raise
#         return json_data

#     # 创建默认推送对象文件
#     def __new_target_json(self) -> None:
#         template_config_path = Path(__file__).resolve(
#         ).parents[2] / "config" / "target.json"
#         if not template_config_path.is_file():
#             raise AppError.Exception(
#                 AppError.TargetNotFound, f"<y>HealthCheck</y>：{template_config_path}下模板配置文件不存在")
#         try:
#             shutil.copy(template_config_path, self.target_path)
#             logger.opt(colors=True).info("<g>HealthCheck</g>：创建空推送对象配置文件成功")
#         except Exception as e:
#             raise AppError.Exception(AppError.IoError, f"创建空推送对象配置文件成功: {e}")

#     # 获取配置文件内容，并载入全局变量
#     def _init_push_target(self, config_data: dict) -> None:
#         try:
#             if not config_data:
#                 raise AppError.Exception(
#                     AppError.ParamNotFound, "意外的空参数！推送用户参数不存在")
#             if config_data.get("GroupPushTarget"):
#                 PUSHTARGET.GroupPushTarget = config_data["GroupPushTarget"]
#             if config_data.get("PrivatePushTarget"):
#                 PUSHTARGET.PrivatePushTarget = config_data["PrivatePushTarget"]
#         except Exception as e:
#             raise AppError.Exception(
#                 AppError.GlobalConfigError, f"推送用户载入全局失败: {e}")

#     # 创建连接检查任务
#     def _create_task(self) -> dict:
#         ping_emby_url = f"{(APPCONFIG.emby_host or '').rstrip("/")}/emby/System/Ping?api_key={(APPCONFIG.emby_key or '')}"
#         info_emby_url = f"{(APPCONFIG.emby_host or '').rstrip("/")}/emby/System/Info?api_key={(APPCONFIG.emby_key or '')}"
#         tmdb_headers = {
#             "accept": "application/json",
#             "Authorization": f"Bearer {(APPCONFIG.tmdb_authorization or '')}"
#         }
#         tasks = {
#             "ping_emby": asyncio.create_task(get_request(ping_emby_url)),
#             "info_emby": asyncio.create_task(get_request(info_emby_url)),
#             "tmdb": asyncio.create_task(get_request("https://api.themoviedb.org/3/authentication",
#                                                     headers=tmdb_headers)),
#             "tmdb_with_proxy": asyncio.create_task(get_request("https://api.themoviedb.org/3/authentication",
#                                                                headers=tmdb_headers,
#                                                                proxy=APPCONFIG.proxy))
#         }
#         return tasks

#     # 获取连接检查任务结果
#     async def _get_tasks_result(self) -> dict:
#         if not self.conntect_task:
#             raise AppError.Exception(AppError.TargetNotFound, "连接检查任务不存在")
#         # 等待所有任务完成
#         results = await asyncio.gather(
#             *self.conntect_task.values(),
#             return_exceptions=True
#         )

#         # 返回 {task_name: result} 字典
#         return {
#             name: res for name, res in zip(self.conntect_task.keys(), results)
#         }

#     # 运行数据库检查
#     async def _run_database_checks(self) -> None:
#         await DBHealthCheck.create_and_check()

#     # 动态导入所有数据处理器
#     async def _import_subclasses(self) -> list[type[AbstractDataProcessor]]:
#         """
#         扫描项目文件夹，动态导入所有模块并查找 AbstractDataProcessor 的子类
#         Returns:
#             list[type[AbstractDataProcessor]]: 找到的所有子类列表
#         Raises:
#             AppError: 如果基类无效或导入过程中发生严重错误
#         """
#         subclasses: list[type[AbstractDataProcessor]] = []
#         base_class = AbstractDataProcessor
#         # 验证基类
#         if not inspect.isclass(base_class):
#             raise AppError.Exception(AppError.UnSupportedType, "基类必须是类对象")
#         # 获取项目根目录
#         project_root = Path(__file__).resolve().parent
#         for file in project_root.rglob("*.py"):
#             # 跳过不需要的文件
#             if file.name == "__init__.py" or file.name.startswith(("test_", "_")):
#                 continue
#             try:
#                 # 转换为模块导入路径
#                 rel_path = file.relative_to(project_root)
#                 module_path = '.'.join(rel_path.with_suffix('').parts)
#                 full_module_path = f"{__package__}.{module_path}"
#                 # 动态导入模块
#                 module = importlib.import_module(full_module_path)
#                 # 检查模块中的类
#                 for _, obj in inspect.getmembers(module, inspect.isclass):
#                     if (issubclass(obj, base_class) and obj is not base_class and obj.__module__ == module.__name__):
#                         subclasses.append(obj)
#                         logger.opt(colors=True).success(
#                             f"找到子类: <y>{obj.__name__}</y> (来自 {module.__name__})")

#             except ImportError as e:
#                 logger.opt(colors=True).warning(
#                     f"模块导入失败: <r>{file.name}</r> - {str(e)}")
#                 continue  # 跳过无法导入的模块而不是终止
#             except Exception as e:
#                 logger.opt(colors=True).error(
#                     f"处理模块时出错: <r>{file}</r> - {str(e)}")
#                 continue  # 记录错误但继续处理其他文件
#         return subclasses

#     # 根据连接结果配置功能开关
#     def _task_result_process(self, task_result: dict) -> None:
#         result_dict = {}
#         if not task_result:
#             raise AppError.Exception(AppError.TargetNotFound, "任务结果不存在")
#         for task_name, task_result in task_result.items():
#             if isinstance(task_result, Exception):
#                 logger.opt(colors=True).warning(
#                     f"AniPusher:任务 {task_name} <y>连接失败类型：{type(task_result).__name__}</y>")
#                 result_dict[task_name] = False
#             else:
#                 result_dict[task_name] = True
#         # Emby功能开关
#         emby_ok = result_dict["ping_emby"] and result_dict["info_emby"]
#         FUNCTION.emby_enabled = emby_ok
#         logger.opt(colors=True).info(
#             "AniPusher:Emby 连接成功，<g>将启用 Emby 功能</g>" if emby_ok else
#             "AniPusher:Emby 连接失败，<y>将禁用 Emby 功能</y>"
#         )

#         # TMDB功能开关
#         if result_dict["tmdb"]:  # 直连成功
#             FUNCTION.tmdb_enabled = True
#             APPCONFIG.proxy = None
#             logger.opt(colors=True).info(
#                 "AniPusher:TMDB 直连成功，<g>将启用 TMDB 功能</g>")
#         elif result_dict["tmdb_with_proxy"]:  # 代理成功
#             FUNCTION.tmdb_enabled = True
#             logger.opt(colors=True).info(
#                 "AniPusher:TMDB 代理连接成功，<g>将启用 TMDB 功能</g>")
#         else:  # 全部失败
#             FUNCTION.tmdb_enabled = False
#             logger.opt(colors=True).warning(
#                 "AniPusher:TMDB 连接失败，<y>将禁用 TMDB 功能</y>")


class NewHealthCheck:
    def __init__(self) -> None:
        self.conntect_task = None

    @classmethod
    async def create_and_run(cls) -> 'NewHealthCheck':
        instance = cls()
        await instance.run_checks()
        return instance

    async def run_checks(self) -> None:
        # 1.读取配置文件,并将配置文件载入全局变量
        self._load_nonebot_config()
        self._load_push_target()
        # 2.创建连接检查任务
        self.conntect_task = self._create_task()
        # 3.数据库检查
        await self._run_database_checks()
        # 4.导入所有数据处理器
        await self._import_subclasses()
        # 获取连接检查任务结果
        task_result = await self._get_tasks_result()
        # 根据连接结果配置功能开关
        self._set_function(task_result)

    # 1.1读取Nonebot配置文件
    def _load_nonebot_config(self) -> None:
        try:
            self.config = get_plugin_config(Config).anipush
            APPCONFIG.emby_host = self.config.emby_host
            APPCONFIG.emby_key = self.config.emby_apikey
            APPCONFIG.tmdb_authorization = self.config.tmdb_apikey
            APPCONFIG.proxy = self.config.tmdb_proxy
        except ValidationError as e:
            logger.opt(colors=True).error(
                f"<r>HealthCheck</r>：配置读取异常!重建配置文件，请重新填写env文件/错误信息：{e}")
            # 重置配置文件
            self._reset_config()
            APPCONFIG.emby_host = None
            APPCONFIG.emby_key = None
            APPCONFIG.tmdb_authorization = None
            APPCONFIG.proxy = None
        except Exception as e:
            raise AppError.Exception(
                AppError.UnknownError, f"配置文件读取失败: {e}")

    # 1.1.1配置文件缺失时重置配置文件
    def _reset_config(self) -> None:
        try:
            path = Path(__file__).resolve().parents[4] / ".env"
            if not path.is_file():
                raise AppError.Exception(
                    AppError.TargetNotFound, f"<r>HealthCheck</r>：{path}下配置文件不存在")
            # 检查并确保 Config 有 anipush 属性
            if not hasattr(Config, "anipush"):
                # 创建默认 AnipushConfig 实例
                Config.anipush = AnipushConfig()
            # 获取必备的配置项
            required_config_list = list(Config.anipush.__fields__.keys())
            # 读取当前的配置
            config = dotenv_values(path)
            # 类型默认值映射
            type_defaults = {
                str: "",
                int: "0",  # dotenv需要字符串形式
                bool: "False",
                float: "0.0",
                list: "[]",
                dict: "{}"
            }
            # 检查配置项是否完整
            for config_item in required_config_list:
                if config_item not in config:
                    type = Config.anipush.__fields__[config_item].type_
                    if type not in type_defaults:
                        raise AppError.Exception(
                            AppError.UnSupportedType, f"不支持的类型: {type}")
                    actual_key = "anipush__" + config_item
                    set_key(path, actual_key, type_defaults[type])
            logger.opt(colors=True).info(
                "<g>HealthCheck</g>: 重置配置文件成功,请前往前往.env文件修改配置并重新启动机器人")
        except Exception as e:
            raise AppError.Exception(
                AppError.UnknownError, f"<r>HealthCheck</r>: 重置配置文件失败: {e}")

    # 1.2载入推送目标
    def _load_push_target(self) -> None:
        path = Path(__file__).resolve().parents[2] / "target.json"
        if not path.is_file():
            # 如果不存在target.json则创建
            self._reset_target_json()
        # 读取推送目标文件
        json_data = JsonIO.read_json(path)
        if not json_data:
            raise AppError.Exception(
                AppError.MissingData, "<r>HealthCheck</r>：意外丢失文件数据!")
        if group_target := json_data.get("GroupPushTarget"):
            PUSHTARGET.GroupPushTarget = group_target
        if private_target := json_data.get("PrivatePushTarget"):
            PUSHTARGET.PrivatePushTarget = private_target

    # 1.2.1重置推送对象文件
    def _reset_target_json(self) -> None:
        try:
            template_path = Path(__file__).resolve(
            ).parents[2] / "config" / "target_tamplate.json"  # 模板文件路径
            target_path = Path(__file__).resolve(
            ).parents[2] / "target.json"  # 目标文件路径
            shutil.copyfile(template_path, target_path)
            logger.opt(colors=True).info(
                "<y>HealthCheck</y>：推送对象文件缺失，已自动创建默认配置文件")
        except FileNotFoundError as e:
            if not template_path.is_file():
                raise AppError.Exception(
                    AppError.TargetNotFound, "<r>HealthCheck</r>：推送对象模板文件缺失!") from e
            else:
                raise AppError.Exception(
                    AppError.UnknownError, f"<r>HealthCheck</r>：推送对象文件创建失败: {e}") from e
        except Exception as e:
            raise AppError.Exception(
                AppError.UnknownError, f"<r>HealthCheck</r>：推送对象文件创建失败: {e}") from e

    # 2.创建连接检查任务
    def _create_task(self) -> dict:
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

    # 2.1获取连接检查任务结果
    async def _get_tasks_result(self) -> dict:
        if not self.conntect_task:
            raise AppError.Exception(AppError.MissingData, "连接检查任务不存在")
        # 等待所有任务完成
        try:
            results = await asyncio.gather(
                *self.conntect_task.values(),
                return_exceptions=True
            )
            # 返回 {task_name: result} 字典
            return {
                name: res for name, res in zip(self.conntect_task.keys(), results)
            }
        except asyncio.CancelledError:
            raise AppError.Exception(
                AppError.UnknownError, "<r>HealthCheck</r>：连接检查任务已取消")
        except Exception as e:
            raise AppError.Exception(
                AppError.UnknownError, f"<r>HealthCheck</r>：连接检查任务异常: {e}") from e

    # 2.2根据连接结果配置功能开关
    def _set_function(self, task_result: dict) -> None:
        try:
            if not task_result:
                raise AppError.Exception(AppError.TargetNotFound, "任务结果不存在")
            result_dict = {}
            for task_name, res in task_result.items():
                try:
                    result_dict[task_name] = not isinstance(res, Exception)
                    if isinstance(res, Exception):
                        logger.opt(colors=True).warning(
                            f"<r>HealthCheck</r>：任务 {task_name} 失败：<y>{type(res).__name__}</y>")
                except Exception as e:
                    logger.error(
                        f"<r>HealthCheck</r>：处理任务 {task_name} 结果时出错: {e}")
                    result_dict[task_name] = False
            try:
                # Emby功能开关
                emby_ok = result_dict.get(
                    "ping_emby", False) and result_dict.get("info_emby", False)
                FUNCTION.emby_enabled = bool(emby_ok)
                logger.opt(colors=True).info(
                    "<g>HealthCheck</g>：Emby 连接成功，<g>将启用 Emby 功能</g>" if emby_ok else
                    "<y>HealthCheck</y>：Emby <r>连接失败</r>，<y>将禁用 Emby 功能</y>"
                )
            except Exception as e:
                logger.error(
                    f"<r>HealthCheck</r>：处理 Emby 功能开关时出错，<y>将禁用 Emby 功能</y>: {e}")
                # 全局回退：确保关键功能被禁用
                FUNCTION.emby_enabled = False
            try:
                # TMDB功能开关
                if result_dict.get("tmdb", False):  # 直连成功
                    FUNCTION.tmdb_enabled = True
                    APPCONFIG.proxy = None
                    logger.opt(colors=True).info(
                        "<g>HealthCheck</g>：TMDB 直连成功，<g>将启用 TMDB 功能</g>")
                elif result_dict.get("tmdb_with_proxy", False):  # 代理成功
                    FUNCTION.tmdb_enabled = True
                    logger.opt(colors=True).info(
                        "<g>HealthCheck</g>：TMDB 代理连接成功，<g>将启用 TMDB 功能</g>")
                else:  # 全部失败
                    FUNCTION.tmdb_enabled = False
                    logger.opt(colors=True).warning(
                        "<y>HealthCheck</y>：TMDB <r>连接失败</r>，<y>将禁用 TMDB 功能</y>")
            except Exception as e:
                logger.error(
                    f"<r>HealthCheck</r>：处理 TMDB 功能开关时出错，<y>将禁用 TMDB 功能</y>: {e}")
                # 全局回退：确保关键功能被禁用
                FUNCTION.tmdb_enabled = False
        except Exception as e:
            # 全局回退：确保关键功能被禁用
            FUNCTION.emby_enabled = False
            FUNCTION.tmdb_enabled = False
            logger.opt(colors=True).error(
                f"<r>HealthCheck</r>：未知错误，<y>将禁用所有功能</y>: {e}")
            raise AppError.Exception(
                AppError.UnknownError,
                f"<r>HealthCheck</r>：{e}"
            ) from e

    # 3.数据库检查
    async def _run_database_checks(self) -> None:
        try:
            await DBHealthCheck.create_and_check()
        except (AppError.Exception, Exception) as e:
            logger.opt(colors=True).error(
                f"<r>HealthCheck</r>：数据库检查失败!:{e}")
            raise

    # 4.动态导入所有数据处理器
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
        project_root = Path(__file__).resolve().parent
        for file in project_root.rglob("*.py"):
            # 跳过不需要的文件
            if file.name == "__init__.py" or file.name.startswith(("test_", "_")):
                continue
            try:
                # 转换为模块导入路径
                rel_path = file.relative_to(project_root)
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
            f"<g>HealthCheck</g>：模块导入成功: {subclasses}")
