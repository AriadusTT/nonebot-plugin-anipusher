import json
from nonebot import logger
from typing import Any
from datetime import datetime
from ...database import DatabaseTables, DatabaseService
from ...utils import CommonUtils, EmbyUtils
from ...exceptions import AppError
from ...config import PUSHTARGET, WORKDIR, FUNCTION, APPCONFIG


class PushService:
    def __init__(self, source: DatabaseTables.TableName):
        self.source = source  # 数据源
        self.tmdb_id = None  # 数据库中未发送数据的TMDBID用于获取Anime库中的数据
        self.id = None  # 数据库中未发送数据的ID,用于最后修改发送状态

    @classmethod
    async def create_and_run(cls, source: DatabaseTables.TableName):
        instance = cls(source)
        await instance.process()
        return instance

    # 主流程
    async def process(self):
        if not self.source or not isinstance(self.source, DatabaseTables.TableName):
            raise AppError.Exception(AppError.ParamNotFound, "未指定数据源或数据源类型错误")
        # 检查是否有未发送的数据
        try:
            db_data = await self._search_unsent_data()
            if isinstance(db_data, list) and len(db_data) == 0:  # 严格验证
                logger.opt(colors=True).info(
                    f"<g>Pusher</g>：{self.source.value} 没有需要推送的数据,等待下一次推送")
                return
            source_data = await self._convert_first_db_row_to_dict(list(db_data), self.source)
        except Exception as e:
            logger.opt(colors=True).error(
                f"<r>Pusher</r>：{e}")
        # 获取TMDB ID
        try:
            self.tmdb_id = self._get_tmdb_id(source_data)
        except Exception as e:
            logger.opt(colors=True).error(
                f"<r>Pusher</r>：{e}")
        # 通过TMDB ID获取Anime库中的数据
        try:
            if not self.tmdb_id:
                logger.opt(colors=True).warning(
                    f"<y>Pusher</y>：{self.source.value} 没有获取到TMDB ID，无法从Anime库中获取数据")
                anime_data = DatabaseTables.get_table_schema(
                    DatabaseTables.TableName.ANIME).copy()
            else:
                anime_db_data = await self._search_in_animedb_by_tmdbid()
                if isinstance(db_data, list) and len(db_data) == 0:
                    logger.opt(colors=True).warning(
                        f"<y>Pusher</y>：{self.tmdb_id} 没有匹配的Anime数据")
                    anime_data = DatabaseTables.get_table_schema(
                        DatabaseTables.TableName.ANIME).copy()
                else:
                    anime_data = await self._convert_first_db_row_to_dict(
                        list(anime_db_data),
                        DatabaseTables.TableName.ANIME)
        except Exception as e:
            logger.opt(colors=True).error(
                f"<r>Pusher</r>：{e}")
        # 将获取到的数据汇总，筛选出推送数据

    async def _search_unsent_data(self):
        try:
            return await DatabaseService.select_data(
                table_name=self.source,
                where={"send_status": 0},
                order_by="id DESC",
                limit=1)
        except Exception as e:
            raise e

    async def _convert_first_db_row_to_dict(self, data: list, source: DatabaseTables.TableName):
        if not data:
            raise AppError.Exception(AppError.ParamNotFound, "意外的异常，数据库数据缺失")
        table_schema = DatabaseTables.generate_default_schema(
            source).copy()
        if len(data) != 1:
            logger.opt(colors=True).warning(
                f"<r>Pusher</r>：{source.value} 数据行数不匹配(预期:1，实际:{len(data)})")
        row_data = data[0]
        if len(row_data) != len(table_schema):  # 检查结构长度是否一致
            raise AppError.Exception(
                AppError.UnknownError, f"数据行字段数不匹配(预期:{len(row_data)}，实际:{len(table_schema)})")
        for key, value in zip(table_schema.keys(), row_data):
            table_schema[key] = value
        return table_schema

    def _get_tmdb_id(self, db_data) -> str | None:
        if not db_data:
            raise AppError.Exception(
                AppError.ParamNotFound, "<r>Pusher</r>：意外的异常，数据库数据缺失")
        if self.source == DatabaseTables.TableName.ANI_RSS:
            return db_data.get("tmdb_id")
        elif self.source == DatabaseTables.TableName.EMBY:
            return db_data.get("tmdb_id")
        else:
            return None

    async def _search_in_animedb_by_tmdbid(self):
        try:
            return await DatabaseService.select_data(
                table_name=DatabaseTables.TableName.ANIME,
                where={"tmdb_id": self.tmdb_id},
                order_by="id DESC")
        except Exception as e:
            raise e

    async def _data_pick(self, source_data, anime_data):
        if not source_data or not anime_data:
            raise AppError.Exception(AppError.ParamNotFound, "意外的异常，缺少必要的参数")
        picker = self.DataPicking(self.source, source_data, anime_data)
        self.data_id = picker._pick_id()
        self.subscriber = picker._pick_subscriber()
        hybrid_image_queue = picker._pick_image_queue()
        picked_data = {
            "title": picker._pick_title(),
            "episode": picker._pick_episode(),
            "episode_title": picker._pick_episode_title(),
            "timestamp": picker._pick_timestamp(),
            "source": picker._pick_source(),
            "action": picker._pick_action(),
            "score": picker._pick_score(),
            "tmdbid": picker._pick_tmdbid()
        }

    # 数据处理类
    class DataPicking:
        def __init__(self,
                     source: DatabaseTables.TableName,
                     source_db_data: dict[str, Any],
                     anime_db_data: dict[str, Any] | None):
            self.source = source
            self.source_db_data = source_db_data
            self.anime_db_data = anime_db_data

        def _pick_id(self) -> int | None:
            if self.source in (DatabaseTables.TableName.ANI_RSS, DatabaseTables.TableName.EMBY):
                if id := self.source_db_data.get("id"):
                    return int(id)
            return None

        def _pick_title(self) -> str | None:
            # 优先从源数据获取标题
            if self.source in (DatabaseTables.TableName.ANI_RSS, DatabaseTables.TableName.EMBY):
                if title := self.source_db_data.get("title"):
                    return title
            # 尝试从Anime数据库获取title
            if self.anime_db_data:
                return self.anime_db_data.get("emby_title") or \
                    self.anime_db_data.get("tmdb_title")
            else:
                logger.opt(colors=True).info("<y>Pusher</y>：没有获取到数据title")
                return None

        def _pick_episode(self) -> str | None:
            if self.source == DatabaseTables.TableName.ANI_RSS:
                season = self.source_db_data.get("season")
                episode = self.source_db_data.get('episode')
            elif self.source == DatabaseTables.TableName.EMBY:
                type_ = self.source_db_data.get('type')
                if not type_:
                    logger.opt(colors=True).warning(
                        f"<y>Pusher</y>：意外的没有获取到{self.source.value}的数据类型")
                    return None
                elif type_ == "movie":
                    return None
                elif type_ == 'Series':
                    merged_episode = self.source_db_data.get('merged_episode')
                    if merged_episode:
                        return f"合计{merged_episode}集更新"
                    else:
                        return None
                elif type_ == 'Episode':
                    season = self.source_db_data.get('season')
                    episode = self.source_db_data.get('episode')
                    if not all([
                            season is not None,
                            episode is not None,
                            str(season).isdigit(),
                            str(episode).isdigit()]):
                        logger.opt(colors=True).warning(
                            f"<y>Pusher</y>：无效的季/集数据n season: {season} episode: {episode}")
                        return None
                    else:
                        # 该断言仅为避免IDE静态类型检查失败
                        assert season is not None and episode is not None
                        return f"S{int(season):02d}-E{int(episode):02d}"

        def _pick_episode_title(self) -> str | None:
            if self.source == DatabaseTables.TableName.ANI_RSS:
                episode_title = (
                    self.source_db_data.get('tmdb_episode_title')
                    or self.source_db_data.get('bangumi_episode_title')
                    or self.source_db_data.get('bangumi_jpepisode_title')
                )
                return episode_title
            if self.source == DatabaseTables.TableName.EMBY:
                return self.source_db_data.get('episode_title')
            else:
                logger.opt(colors=True).info(
                    "<y>Pusher</y>：没有获取到数据episode_title")
                return None

        def _pick_timestamp(self) -> str | None:
            if self.source in (DatabaseTables.TableName.ANI_RSS, DatabaseTables.TableName.EMBY):
                timestamp = self.source_db_data.get('timestamp')
                if timestamp:
                    return datetime.fromisoformat(timestamp).strftime('%m-%d %H:%M:%S')
                else:
                    logger.opt(colors=True).info(
                        "<y>Pusher</y>：没有获取到数据时间戳")
                    return None
            else:
                logger.opt(colors=True).info("<y>Pusher</y>：没有获取到数据timestamp")
                return None

        def _pick_source(self) -> str:
            return self.source.value

        def _pick_action(self) -> str | None:
            if self.source == DatabaseTables.TableName.ANI_RSS:
                return self.source_db_data.get('action')
            elif self.source == DatabaseTables.TableName.EMBY:
                return "媒体库更新完成"
            else:
                logger.opt(colors=True).info("<y>Pusher</y>：没有获取到数据action")
                return None

        def _pick_score(self) -> str | None:
            score = None
            if self.source == DatabaseTables.TableName.ANI_RSS:
                score = self.source_db_data.get('score')
            elif self.source == DatabaseTables.TableName.EMBY:
                pass
            if score is not None:
                return score
            # 如果没有score则尝试降级从Anime数据库获取score
            if self.anime_db_data:
                score = self.anime_db_data.get('score')
            if score is not None:
                return score
            else:
                logger.opt(colors=True).info('<y>Pusher</y>：没有获取到数据score')
                return None

        def _pick_tmdbid(self) -> str | None:
            if self.source in (DatabaseTables.TableName.ANI_RSS, DatabaseTables.TableName.EMBY):
                if tmdb_id := self.source_db_data.get('tmdb_id'):
                    return tmdb_id
            if self.anime_db_data:
                if tmdb_id := self.anime_db_data.get('tmdb_id'):
                    return tmdb_id
            logger.opt(colors=True).info('Pusher：<y>未获取到tmdb_id！</y>')
            return None

        def _pick_subscriber(self) -> tuple[dict[Any, Any], list[str]]:
            '''
            获取订阅者
            订阅者在Anime数据库中
            分为2个column
            1. group_subscriber: 群组订阅者,结构为{'group_id': [user_id, user_id, ...]}
            2. private_subscriber: 私人订阅者，结构为[user_id, user_id, ...]
            '''
            if not self.anime_db_data:
                logger.opt(colors=True).info(
                    "<y>Pusher</y>：无法获取订阅者，没有Anime表数据")
                return ({}, [])
            try:
                group_subscriber = json.loads(
                    self.anime_db_data.get('group_subscriber', {}))
                private_subscriber = json.loads(
                    self.anime_db_data.get('private_subscriber', []))
            except Exception as e:
                logger.opt(colors=True).info(
                    f"<y>Pusher</y>：无法获取订阅者，JSON解析错误: {e}")
                return ({}, [])
            return (group_subscriber, private_subscriber)

        def _pick_image_queue(self) -> list:
            '''
                获取图片队列
                1. 从Anime数据库中获取emby_series_tag
                2. 从Source数据库中获取series_tag
                3. 从Anime数据库中获取ani_rss_image
                4. 从Source数据库中获取image_url
                5. 优先级为1 > 2 > 3 > 4

                返回一个图片队列（tag非url，而是emby的tag）
                如果没有获取到图片，则返回空列表

            '''
            # 定义优先级采集顺序
            image_sources = [
                # (数据源, 字段名, 条件)
                (self.anime_db_data, "emby_series_tag", True),
                (self.source_db_data, "series_tag",
                 self.source == DatabaseTables.TableName.EMBY),
                (self.anime_db_data, "ani_rss_image", True),
                (self.source_db_data, "image_url",
                 self.source == DatabaseTables.TableName.ANI_RSS)
            ]
            seen = set()  # 用于记录已经添加过的图片
            image_queue = []  # 初始化图片队列
            for source, field, condition in image_sources:
                if not condition or not source:
                    continue
                if item := source.get(field):
                    if item not in seen:
                        seen.add(item)
                        image_queue.append(item)
            return image_queue

        def _pick_series_id(self) -> str | None:  # 获取series_id,只有emby有，用于获取emby图片
            if self.source == DatabaseTables.TableName.EMBY:
                return self.source_db_data.get('series_id')
            else:
                return None
    # 处理图片队列，最终返回一个base64编码的可以图片信息

    class ImageQueueProcess:
        def __init__(self, image_queue: list, emby_series_id: str | None = None, tmdb_id: str | None = None) -> None:
            self.image_queue = image_queue
            self.emby_series_id = emby_series_id
            self.tmdb_id = tmdb_id

        async def process(self):
            if not self.image_queue:
                logger.opt(colors=True).info('<y>Pusher</y>：没有获取到可用图片，使用默认图片')
                return self._default_image()
            url_queue = []  # 存储图片url
            for item in self.image_queue:  # 遍历图片队列
                if CommonUtils.is_url(str(item)):
                    url_queue.append(item)
                else:
                    # 如果不是url，则为emby的tag，需要转换为url
                    if not FUNCTION.emby_enabled:
                        continue
                    try:
                        url = EmbyUtils.splice_emby_image_url(
                            APPCONFIG.emby_host, self.emby_series_id, item)
                        url_queue.append(url)
                    except Exception as e:
                        logger.opt(colors=True).warning(
                            f"<y>Pusher</y>：获取emby图片失败，错误信息：{e}")
            unique_url_queue = list(dict.fromkeys(url_queue))  # 去重
            if not unique_url_queue:
                logger.opt(colors=True).info('<y>Pusher</y>：没有获取到可用图片，使用默认图片')
                return self._default_image()

        # 在本地存储中查找图片，如果找不到则下载
        def _search_in_localstore(self):
            try:
                if not self.tmdb_id:
                    raise AppError.Exception(
                        AppError.MissingData, "项目TMDB ID缺失！")
                if not WORKDIR.cache_dir:
                    raise AppError.Exception(AppError.MissingData, "项目缓存目录缺失！")
                local_img_path = WORKDIR.cache_dir / f"{self.tmdb_id}.jpg"
                # 如果本地存在图片，且未过期，则直接返回base64编码
                if not local_img_path.exists():
                    return None
                # 如果图片未过期，则直接返回base64编码
                if not CommonUtils.is_cache_img_expired(local_img_path):
                    return CommonUtils.img_to_base64(local_img_path)
                # 如果本地存在图片，但已过期，则删除并重新下载
                local_img_path.unlink()
                logger.opt(colors=True).info(
                    '<g>Pusher</g>：本地图片<y>已过期</y>，重新下载')
                return None
            except Exception as e:
                logger.opt(colors=True).warning(
                    f"<y>Pusher</y>：获取本地图片失败，错误信息：{e}")
                return None

        # 获取默认图片

        def _default_image(self):
            try:
                if not WORKDIR.cache_dir:
                    raise AppError.Exception(AppError.MissingData, "项目缓存目录缺失！")
                img_path = WORKDIR.cache_dir / "res" / "default.jpg"
                return CommonUtils.img_to_base64(img_path)
            except Exception as e:
                logger.opt(colors=True).warning(
                    f"<y>Pusher</y>：获取默认图片失败，错误信息：{e}")
                return None
