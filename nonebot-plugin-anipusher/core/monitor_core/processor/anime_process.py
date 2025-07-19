
from ....database import DatabaseManager, DatabaseTables, GeneralDatabaseOperate
from ....constants.error_handling import AppError
from ....config.global_config import FUNCTION, APPCONFIG
from ....others.utils import PublicUtils
from nonebot import logger


class AnimeProcess:
    """
    Anime数据处理类
    处理Anime相关数据，提取必要信息并进行格式化
    """

    def __init__(self, data: dict, data_source: DatabaseTables.TableName):
        self.data = data
        self.tmdb_id = None
        self.data_source = data_source
        self.reformated_data = None
        self.db_data = {}
        self.merged_data = None
        self.conn = None

    async def process(self):
        """
        处理Anime数据
        返回处理后的Anime数据
        """
        if not self.data:
            raise ValueError("待处理的数据不能为空")
        if not isinstance(self.data, dict):
            raise TypeError(f"待处理的数据类型错误：{type(self.data)}")
        if not self.data_source:
            raise ValueError("数据源不能为空")
        if not isinstance(self.data_source, DatabaseTables.TableName):
            raise TypeError(f"数据源类型错误：{type(self.data_source)}")
        # 从传入的data中提取必要信息
        self.reformated_data = await self._reformat()  # 数据格式化
        self.tmdb_id = self.reformated_data.get("tmdb_id")  # 获取tmdb_id
        if not self.tmdb_id:
            raise AppError.Exception(
                AppError.ParamNotFound, "tmdb_id不能为空，无法进行后续处理")
        # 数据库操作
        with DatabaseManager.get_connection() as self.conn:  # 获取数据库连接
            if not self.conn:
                raise AppError.Exception(
                    AppError.DatabaseInitError, "无法获取数据库连接")
            # 数据库操作
            self.db_data = self._db_data_to_dict(
                await self._get_data_from_database())  # 获取数据库数据并转换为字典
            # logger.opt(colors=True).info(f"{self.data_source.value}:数据库数据重组完成：{self.db_data}")
            if self.db_data:  # 如果有数据库数据
                self._merge_data()  # 数据合并
                # logger.opt(colors=True).info(f"{self.data_source.value}:数据合并完成：{self.merged_data}")
            else:
                raise AppError.Exception(
                    AppError.UnknownError, "未生成模板数据，无法进行后续处理")
            # 数据库操作
            await self._insert_data_into_database()  # 数据插入或更新
        return self.merged_data

    async def _reformat(self):
        """
        数据格式化
        提取必要信息并生成格式化后的数据
        """
        try:
            extract = self.DataExtraction(
                self.data, self.data_source)  # 初始化数据提取类
            # 配置默认项
            default_dict = DatabaseTables.generate_default_dict(
                DatabaseTables.TableName.ANIME)  # 获取默认模板结构
            default_dict.update({
                "id": None,  # 配置默认发送状态
                "emby_title": extract.extract_emby_title(),
                "tmdb_title": extract.extract_tmdb_title(),
                "tmdb_id": extract.extract_tmdb_id(),
                "score": extract.extract_score(),
                "tmdb_url": extract.extract_tmdb_url(),
                "bangumi_url": extract.extract_bgm_url(),
                "ani_rss_image": await extract.extract_ani_rss_image(),
                "emby_series_tag": await extract.extract_emby_series_tag(),
                "emby_series_url": extract.extract_emby_series_url(),
                "group_subscriber": extract.extract_subscriber(),
                "private_subscriber": extract.extract_subscriber()
            })
            return default_dict
        except (AppError.Exception, Exception) as e:
            raise AppError.Exception(
                AppError.UnknownError, f"{self.data_source.value}：数据格式化异常：{e}")

    class DataExtraction:
        def __init__(self, data: dict, data_source: DatabaseTables.TableName):
            self.data = data
            self.data_source = data_source

        def extract_emby_title(self) -> str | None:
            if self.data_source == DatabaseTables.TableName.EMBY:
                return self.data.get("title")
            elif self.data_source == DatabaseTables.TableName.ANI_RSS:
                return None
            else:
                return None

        def extract_tmdb_title(self) -> str | None:
            if self.data_source == DatabaseTables.TableName.EMBY:
                return None
            elif self.data_source == DatabaseTables.TableName.ANI_RSS:
                return self.data.get("tmdb_title")
            else:
                return None

        def extract_tmdb_id(self) -> int | None:
            if self.data_source == DatabaseTables.TableName.EMBY:
                return self.data.get("tmdb_id")
            elif self.data_source == DatabaseTables.TableName.ANI_RSS:
                return self.data.get("tmdb_id")
            else:
                return None

        def extract_score(self) -> str | None:
            if self.data_source == DatabaseTables.TableName.EMBY:
                return None
            elif self.data_source == DatabaseTables.TableName.ANI_RSS:
                return self.data.get("score")
            else:
                return None

        def extract_tmdb_url(self) -> str | None:
            if self.data_source == DatabaseTables.TableName.EMBY:
                return None
            elif self.data_source == DatabaseTables.TableName.ANI_RSS:
                return self.data.get("tmdb_url")
            else:
                return None

        def extract_bgm_url(self) -> str | None:
            if self.data_source == DatabaseTables.TableName.EMBY:
                return None
            elif self.data_source == DatabaseTables.TableName.ANI_RSS:
                return self.data.get("bangumi_url")
            else:
                return None

        async def extract_ani_rss_image(self) -> str | None:
            if self.data_source == DatabaseTables.TableName.EMBY:
                return None
            elif self.data_source == DatabaseTables.TableName.ANI_RSS:
                return self.data.get("image_url")

        async def extract_emby_series_tag(self) -> str | None:
            if self.data_source == DatabaseTables.TableName.EMBY:
                return self.data.get("series_tag")
            elif self.data_source == DatabaseTables.TableName.ANI_RSS:
                return None
            else:
                return None

        def extract_emby_series_url(self) -> str | None:
            if self.data_source == DatabaseTables.TableName.EMBY:
                host = APPCONFIG.emby_host
                series_id = self.data.get("series_id")
                server_id = self.data.get("server_id")
                if not FUNCTION.emby_enabled:
                    logger.opt(colors=True).info(
                        f"{self.data_source.value}:未启用Emby功能，无法获取Emby系列链接")
                    return None
                try:
                    return PublicUtils.get_emby_series_url(host, series_id, server_id)
                except Exception as e:
                    logger.opt(colors=True).warning(
                        f"<y>{self.data_source.value}</y>：获取Emby系列链接异常：{e}")
                    return None
            elif self.data_source == DatabaseTables.TableName.ANI_RSS:
                return None
            else:
                return None

        def extract_subscriber(self) -> str | None:
            return None

    async def _get_data_from_database(self) -> tuple:
        """
        从数据库中获取指定tmdb_id的数据
        Args:
            table_name: 数据库表名
            tmdb_id: tmdb_id
        Returns:
            数据字典
        """
        if not self.tmdb_id:
            raise AppError.Exception(
                AppError.ParamNotFound, "tmdb_id不能为空")
        if not self.conn:
            raise AppError.Exception(
                AppError.DatabaseInitError, "未能获取数据库连接")
        db_data = await GeneralDatabaseOperate.select_data(
            self.conn,
            DatabaseTables.TableName.ANIME,
            where={"tmdb_id": self.tmdb_id}
        )
        if not db_data:
            logger.opt(colors=True).warning(
                f"{self.data_source.value}：未在数据库中找到tmdb_id:{self.tmdb_id}的数据")
            return ()
        if not isinstance(db_data, list) or len(db_data) == 0:
            logger.opt(colors=True).warning(
                f"{self.data_source.value}：查询结果异常，未找到任何数据")
            return ()
        if len(db_data) > 1:
            logger.opt(colors=True).warning(
                f"{self.data_source.value}：查询结果异常，找到多条数据，取第一条")
            return ()
        return db_data[0]

    def _db_data_to_dict(self, db_data: tuple) -> dict:
        """
        将数据库查询结果转换为字典
        Args:
            db_data: 数据库查询结果元组
        Returns:
            数据字典
        """
        default_dict = DatabaseTables.generate_default_dict(
            DatabaseTables.TableName.ANIME)  # 获取默认模板结构
        if not db_data:
            logger.opt(colors=True).warning(
                f"{self.data_source.value}：未在数据库中找到相关数据，使用默认模板")
            return default_dict

        if len(db_data) != len(default_dict):
            raise AppError.Exception(
                AppError.DatabaseDaoError, "数据库查询结果与默认结构不匹配")
        for key, value in zip(default_dict.keys(), db_data):
            default_dict[key] = value
        return default_dict

    def _merge_data(self):
        """
        合并数据
        将格式化后的数据与数据库中的数据进行合并
        """
        if not self.reformated_data:
            raise AppError.Exception(
                AppError.ParamNotFound, "reformated_data不能为空")
        if not self.db_data:
            logger.opt(colors=True).warning(
                f"{self.data_source.value}：未在数据库中找到相关数据，使用reformated_data作为合并结果")
            self.merged_data = self.reformated_data
            return
        # 合并逻辑：将reformated_data中的非空字段覆盖db_data中的对应字段
        default_dict = DatabaseTables.generate_default_dict(
            DatabaseTables.TableName.ANIME)  # 获取默认模板结构
        force_fields = ["subscriber"]
        for key in default_dict:
            if key in force_fields:
                default_dict[key] = self.db_data[key]
                continue
            if self.reformated_data[key] is not None:
                default_dict[key] = self.reformated_data[key]
            else:
                default_dict[key] = self.db_data[key]
        self.merged_data = default_dict

    async def _insert_data_into_database(self):
        if not self.merged_data:
            raise AppError.Exception(
                AppError.ParamNotFound, "数据合并异常,没有合并后的数据")
        if not self.conn:
            raise AppError.Exception(
                AppError.DatabaseInitError, "未能获取数据库连接")
        await GeneralDatabaseOperate.insert_or_update_data(
            self.conn,
            DatabaseTables.TableName.ANIME,
            self.merged_data,
            conflict_columns=["tmdb_id"]
        )
