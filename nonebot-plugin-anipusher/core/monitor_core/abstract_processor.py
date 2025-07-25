from abc import ABC, abstractmethod
from nonebot import logger

from ...database import DatabaseManager, DatabaseTables, GeneralDatabaseOperate
from ...constants.error_handling import AppError
from ..push_core import Pusher


class AbstractDataProcessor(ABC):  # 数据处理基类
    _registry = {}  # 注册器

    def __init__(self, data, source: DatabaseTables.TableName):
        self.raw_data = data    # 从webhook获取的数据
        self.source: DatabaseTables.TableName = source  # 解析到的数据源
        self.reformated_data = None  # 整形化后的数据
        self.db_data = None  # 数据库数据
        self.tmdb_id = None  # TMDB ID
        self.conn = None    # 数据库连接

    @classmethod
    def register(cls, source_type):
        """装饰器：将子类注册到指定类型"""
        def wrapper(subclass):
            cls._registry[source_type] = subclass
            return subclass
        return wrapper

    @classmethod
    async def select_processor(cls, data, source):
        """根据 source 选择对应的处理器"""
        subclass = cls._registry.get(source)
        if subclass:
            return subclass(data, source)
        return None

    # 主处理流程
    async def execute(self):
        """
        执行完整处理流程
        1. 数据格式化
        2. 数据持久化
        3. 可选项：Anime数据处理
        4. 数据推送
        """
        # 数据格式化
        try:
            await self._reformat()
        except (AppError.Exception, Exception) as e:
            logger.opt(colors=True).error(f"<r>{self.source.value}</r>：数据格式化异常：{e}")
            return
        # 数据持久化
        try:
            await self._datapersistence()
        except (AppError.Exception, Exception) as e:
            logger.opt(colors=True).error(f"<r>{self.source.value}</r>：数据持久化异常：{e}")
            return
        # 可选项：Anime数据处理
        try:
            if self._enable_anime_process():
                await self._anime_process()
                logger.opt(colors=True).info(
                    f"<g>{self.source.value}</g>：Anime数据处理成功")
            else:
                logger.opt(colors=True).info(
                    f"</g>{self.source.value}</g>：未启用Anime数据处理")
        except (AppError.Exception, Exception) as e:
            logger.opt(colors=True).error(
                f"<r>{self.source.value}</r>：Anime数据处理异常：{e}")
        # 数据推送
        try:
            await self._push()
        except (AppError.Exception, Exception) as e:
            logger.opt(colors=True).error(f"<r>{self.source.value}</r>：推送异常：{e}")

    # 数据持久化
    async def _datapersistence(self):
        if not self.reformated_data:
            raise AppError.Exception(
                AppError.ParamNotFound, f"<r>{self.source.value}</r>：待持久化的数据为空")
        try:
            with DatabaseManager.get_connection() as self.conn:
                await GeneralDatabaseOperate.insert_or_update_data(
                    self.conn, self.source, self.reformated_data)
            logger.opt(colors=True).info(
                f"<g>{self.source.value}</g>：数据持久化成功")
        except (AppError.Exception, Exception) as e:
            raise e

    # 可选项，启用Anime数据处理
    def _enable_anime_process(self):
        return False

    # 可选项，Anime数据处理
    async def _anime_process(self):
        if not self.tmdb_id:
            logger.opt(colors=True).warning(
                f"<y>{self.source.value}</y>：未获取到TMDB ID，跳过Anime数据处理")
            return
        if not self.reformated_data:
            logger.opt(colors=True).warning(
                f"<y>{self.source.value}</y>：待处理的数据为空，跳过Anime数据处理")
            return
        from .processor.anime_process import AnimeProcess
        try:
            anime_process = AnimeProcess(
                self.reformated_data, self.source)
            self.db_data = await anime_process.process()
        except Exception as e:
            raise e

    # 数据推送
    async def _push(self) -> None:
        await Pusher.create_and_run(self.source)

    # 需要子类实现的抽象方法
    # 数据格式化
    @abstractmethod
    async def _reformat(self) -> bool:
        pass
