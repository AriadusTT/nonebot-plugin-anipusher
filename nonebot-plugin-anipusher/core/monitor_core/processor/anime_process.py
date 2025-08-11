
from nonebot import logger
from ....exceptions import AppError
from ....database import DatabaseTables, DatabaseService
from ....config import APPCONFIG, FUNCTION
from ....utils import EmbyUtils


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
        try:
            # 验证参数
            self._param_validation()
            # 数据格式化
            self.reformated_data = await self._reformat()
            self.tmdb_id = self.reformated_data.get("tmdb_id")  # 获取tmdb_id
            # 如果没有tmdb_id，则跳过后续处理
            if not self.tmdb_id:
                raise AppError.Exception(
                    AppError.ParamNotFound, "没有获取到TMDB ID")
            # 数据库查询,并转换为字典
            self.db_data = self._convert_db_tuple_to_dict(await self._get_data_from_database())
            # 数据合并
            self._merge_to_anime_schema()
            # 数据更新
            await self._update_to_database()
            logger.opt(colors=True).info(
                f"<g>{self.data_source.value}</g>：数据持久化 <g>完成</g>")
        except Exception as e:
            raise e

    def _param_validation(self):
        if not self.data:
            raise AppError.Exception(AppError.ParamNotFound, "意外的异常，参数缺失")
        if not self.data_source:
            raise AppError.Exception(AppError.ParamNotFound, "意外的异常，数据源缺失")
        if not isinstance(self.data, dict):
            raise AppError.Exception(AppError.UnSupportedType, "参数类型错误")
        if not isinstance(self.data_source, DatabaseTables.TableName):
            raise AppError.Exception(AppError.UnSupportedType, "数据源类型错误")

    async def _reformat(self):
        """
        数据格式化
        提取必要信息并生成格式化后的数据
        """
        try:
            extract = self.DataExtraction(
                self.data, self.data_source)  # 初始化数据提取类
            # 配置默认项
            default_schame = DatabaseTables.generate_default_schema(
                DatabaseTables.TableName.ANIME).copy()  # 获取默认模板结构
            default_schame.update({
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
                "group_subscriber": None,
                "private_subscriber": None
            })
            return default_schame
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
                    return EmbyUtils.splice_emby_series_url(host, series_id, server_id)
                except Exception as e:
                    logger.opt(colors=True).warning(
                        f"<y>{self.data_source.value}</y>：获取Emby系列链接异常：{e}")
                    return None
            elif self.data_source == DatabaseTables.TableName.ANI_RSS:
                return None
            else:
                return None

    async def _get_data_from_database(self) -> tuple:
        try:
            db_data = await DatabaseService.select_data(
                table_name=DatabaseTables.TableName.ANIME,
                where={"tmdb_id": self.tmdb_id})
        except Exception as e:
            logger.opt(colors=True).error(
                f"{DatabaseTables.TableName.ANIME.value}：从数据库获取数据异常：{e}")
            return ()
        if not isinstance(db_data, list):
            logger.opt(colors=True).error(
                f"{DatabaseTables.TableName.ANIME.value}：从数据库获取数据类型错误")
            return ()
        if not db_data:
            logger.opt(colors=True).warning(
                f"{DatabaseTables.TableName.ANIME.value}：从数据库获取数据为空")
            return ()
        if len(db_data) > 1:
            logger.opt(colors=True).error(
                f"{DatabaseTables.TableName.ANIME.value}：ANIME表数据异常，tmdb_id重复,请检查数据库")
            logger.opt(colors=True).info(
                f"{DatabaseTables.TableName.ANIME.value}：默认选择第一个数据")
        return db_data[0]

    def _convert_db_tuple_to_dict(self, db_data: tuple) -> dict:
        """
        将数据库查询结果转换为字典
        Args:
            db_data: 数据库查询结果元组
        Returns:
            数据字典
        """
        table_schema = DatabaseTables.generate_default_schema(
            DatabaseTables.TableName.ANIME)  # 获取默认模板结构
        if not db_data:
            return table_schema.copy()
        if len(db_data) != len(table_schema):
            raise AppError.Exception(
                AppError.DatabaseDaoError, f"数据行字段数不匹配(预期:{len(table_schema)}，实际:{len(db_data)})")
        for key, value in zip(table_schema.keys(), db_data):
            table_schema[key] = value
        return table_schema

    def _merge_to_anime_schema(self) -> None:
        """
        将数据合并到anime表结构中
        Returns:
            anime表结构
        """
        force_fields = ["group_subscriber",
                        "private_subscriber"]  # 强制维持字段，该些字段不会从新数据中获取
        anime_schema = DatabaseTables.generate_default_schema(
            DatabaseTables.TableName.ANIME).copy()  # 获取默认模板结构
        if not self.reformated_data:
            raise AppError.Exception(
                AppError.MissingData, "格式化数据为空，无法合并到anime表结构中")
        for key in anime_schema:
            if key in force_fields:
                anime_schema[key] = self.db_data[key]
                continue
            if self.reformated_data[key] is not None:
                anime_schema[key] = self.reformated_data[key]
            else:
                anime_schema[key] = self.db_data[key]
        self.merged_data = anime_schema
        logger.opt(colors=True).info(
            f"<g>{self.data_source.value}</g>：Anime数据合并 <g>完成</g>，等待数据持久化")

    async def _update_to_database(self) -> None:
        """
        更新数据库
        Returns:
            None
        """
        if not self.merged_data:
            raise AppError.Exception(
                AppError.MissingData, "合并数据为空，无法更新数据库")
        await DatabaseService.upsert_data(DatabaseTables.TableName.ANIME,
                                          self.merged_data,
                                          conflict_columns=["tmdb_id"])
