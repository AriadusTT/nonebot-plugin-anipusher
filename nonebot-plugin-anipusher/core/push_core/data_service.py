import json
from datetime import datetime
from nonebot import logger
from typing import Any

from ...database import DatabaseTables


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
                self.anime_db_data.get('group_subscriber') or '{}')
            private_subscriber = json.loads(
                self.anime_db_data.get('private_subscriber') or '[]')
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
