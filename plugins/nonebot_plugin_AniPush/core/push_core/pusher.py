from pathlib import Path
import json
from datetime import datetime
from typing import Any
from nonebot import logger
from .fill import fill_message, fill_img, fill_at
from .push import group_msg_pusher, private_msg_pusher
from .message_template import MessageTemplate
from ...constants.error_handling import AppError
from ...config import PUSHTARGET, FUNCTION, APPCONFIG
from ...others.utils import PublicUtils
from ...database import DatabaseTables, GeneralDatabaseOperate, DatabaseManager
from ...external import ImageVerification


class Pusher:
    def __init__(self, source: DatabaseTables.TableName):
        self.source = source
        self.conn = DatabaseManager.get_connection()
        self.tmdb_id = None
        self.source_db_dict = {}
        self.anime_db_dict = {}
        self.target = ()
        self.image_queue = []
        self.subscriber = ()
        self.data_id = None

    @classmethod
    async def create_and_run(cls, source: DatabaseTables.TableName):
        instance = cls(source)
        await instance.process()
        return instance

    # 主流程
    async def process(self):
        # 主数据处理流程
        # 1.从Source数据库获取数据,并结构化为dict结构
        db_data = await self._rebuild_data_dict(
            await self._get_data_from_source_db(),
            self.source
        )
        if not db_data:
            logger.opt(colors=True).info("<y>Pusher</y>：未查询到待发送数据！等待下一次推送")
            return
        # 2.获取Tmdb_id
        self.tmdb_id = self._get_tmdb_id(db_data)
        # 3.如果获取到了Tmdb_id从Anime数据库获取tmdb_id数据，并重新组装为dict结构
        if self.tmdb_id:
            anime_db_data = await self._rebuild_data_dict(
                await self._get_data_from_anime_db(self.tmdb_id),
                DatabaseTables.TableName.ANIME
            )
        else:
            logger.opt(colors=True).info(
                "<y>Pusher</y>：未获取到tmdb_id！无法从Anime数据库获取数据！")
        # 4.获取推送目标
        self.target = self._get_push_target()
        # 5.将获取到的2个数据汇总，重组为dict结构
        self.source_db_dict = db_data
        self.anime_db_dict = anime_db_data
        picked_data = await self._data_pick()
        # 6.合成base图片流
        base64_img = PublicUtils.get_base64_img_url(self.image_queue[0])
        # 7.合成推送主体
        msg = self._msg_fill(picked_data, base64_img)
        # 8.推送
        await self._push(msg)
        # 9.重置发送状态
        await self._change_send_status()
        # 10.关闭数据库连接
        self.conn.close()
        logger.opt(colors=True).info(
            f"<g>Pusher</g>：{self.source.value}源，{self.tmdb_id}推送任务完成！")

    # 从Source数据库获取未发送的数据
    async def _get_data_from_source_db(self):
        db_data = await GeneralDatabaseOperate.select_data(
            self.conn,
            self.source,
            [],
            {"send_status": 0},
            "id DESC",
            1,
        )
        return db_data

    # 从Anime数据库获取数据，需要传入tmdb_id
    async def _get_data_from_anime_db(self, tmdb_id: str):
        db_data = await GeneralDatabaseOperate.select_data(
            self.conn,
            DatabaseTables.TableName.ANIME,
            [],
            {"tmdb_id": tmdb_id}
        )
        return db_data

    # 将数据库获取的数据重新组装为DatabaseTables.TableName定义的结构
    async def _rebuild_data_dict(self,
                                 db_data: list,
                                 source: DatabaseTables.TableName) -> dict[Any, Any]:
        """将数据库获取的数据重新组装为DatabaseTables.TableName定义的结构。

        Args:
            db_data (list): 从数据库获取的原始数据列表。
            source (DatabaseTables.TableName): 数据表名称枚举，用于生成默认数据结构。

        Returns:
            dict[Any, Any]: 组装后的数据字典，键为表字段名，值为对应数据，如果没有原始数据则返回空{}。

        Raises:
            AppError.Exception: 如果未获取到数据表默认配置、数据类型不支持或数据长度不匹配时抛出异常。
        """
        if not db_data:
            return {}
        def_dict = DatabaseTables.generate_default_dict(source)
        if not def_dict:
            raise AppError.Exception(
                AppError.MissingData, f"<y>Pusher</y>：未获取到数据表 {source.value} 默认配置！")
        if not isinstance(db_data[0], (dict, list, tuple)):
            raise AppError.Exception(
                AppError.UnSupportedType, f"<y>Pusher</y>：意料外的数据类型：{type(db_data[0])}")
        if len(db_data[0]) != len(def_dict):
            raise AppError.Exception(
                AppError.UnSupportedType, f"<y>Pusher</y>：数据长度不匹配！（表定义: {len(def_dict)}，实际: {len(db_data[0])}）")
        # 数据类型为dict时处理
        if isinstance(db_data[0], dict):
            return_dict = {}
            for key in def_dict.keys():
                if key not in db_data[0]:
                    logger.opt(colors=True).warning(
                        f"<y>Pusher</y>：数据表{source.value}中缺少字段：<y>{key}！</y>")
                    continue
                return_dict[key] = db_data[0].get(key)
            return return_dict
        # 数据类型为list/Tuple时处理
        return dict(zip(def_dict.keys(), db_data[0]))

    # 从数据源的db_data数据获取tmdb_id
    def _get_tmdb_id(self, db_data) -> str | None:
        if not db_data:
            raise AppError.Exception(
                AppError.MissingData, "<r>Pusher</r>：错误的空数据！当前源数据不应为空！")
        if self.source == DatabaseTables.TableName.ANI_RSS:
            return db_data.get("tmdb_id")
        elif self.source == DatabaseTables.TableName.EMBY:
            return db_data.get("tmdb_id")
        else:
            return None

    # 将获取到的数据汇总，筛选出推送数据
    async def _data_pick(self):
        if not self.source_db_dict:
            raise AppError.Exception(
                AppError.MissingData, "<r>Pusher</r>：错误的空数据！当前源数据不应为空！")
        picker = self.DataPicking(
            self.source, self.source_db_dict, self.anime_db_dict, self.target)
        self.data_id = picker._pick_id()
        if not self.data_id:
            raise AppError.Exception(
                AppError.ParamNotFound, "Pusher：未获取到可用的id标识，无法重置发送状态，任务取消!")
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
        # 获取ID
        self.data_id = picker._pick_id()
        # 获取订阅者
        self.subscriber = picker._pick_subscriber()
        # 获取图片队列
        hybrid_image_queue = picker._pick_image_queue()
        # 初始化队列处理器，处理图片队列
        queue_processor = self.ImageQueueProcess(
            hybrid_image_queue, picker._pick_series_id())
        self.image_queue = await queue_processor.process()
        return picked_data

    # 拼接消息
    def _msg_fill(self, picked_data: dict[str, Any], base64_image: str):
        if not picked_data:
            raise AppError.Exception(
                AppError.MissingData, "<r>Pusher</r>：错误的空数据！填充数据不应为空！")
        if not base64_image:
            raise AppError.Exception(
                AppError.MissingData, "<r>Pusher</r>错误的空数据！图片流数据不应为空！")
        # 初始化msg
        msg = []
        msg_head = fill_message(MessageTemplate.PUSH_HEAD, None)
        msg.append(msg_head)
        # 填充img
        msg.append(fill_img(base64_image))
        msg_body = fill_message(MessageTemplate.PUSH_BODY, picked_data)
        msg.append(msg_body)
        return msg

    # 获取推送目标
    def _get_push_target(self) -> tuple[list, list]:
        group_target = PUSHTARGET.GroupPushTarget.get(
            self.source.value, []) if PUSHTARGET.GroupPushTarget else []
        private_target = PUSHTARGET.PrivatePushTarget.get(
            self.source.value, []) if PUSHTARGET.PrivatePushTarget else []
        return (group_target, private_target)

    # 推送消息
    async def _push(self, msg: list):
        if len(self.target) != 2:
            raise AppError.Exception(
                AppError.InvalidLength, "<r>Pusher</r>：错误的推送目标结构！")
        if not msg:
            raise AppError.Exception(
                AppError.ParamNotFound, "<r>Pusher</r>：错误的空数据！当前消息数据不应为空！")
        # 将其重置为空字典
        if not self.subscriber:
            group_subscriber = {}
            private_subscriber = []
        else:
            group_subscriber = self.subscriber[0]
            private_subscriber = self.subscriber[1]
        # 参数配置
        group_target = self.target[0]
        private_target = self.target[1]
        try:
            for id in group_target:
                push_msg = msg.copy()
                subscriber = group_subscriber.get(id, [])
                if subscriber:
                    push_msg.append(fill_message(
                        MessageTemplate.Subscriber, None))
                    for user in subscriber:
                        push_msg.append(fill_at(int(user)))
                await group_msg_pusher(push_msg, [id])
                logger.opt(colors=True).info(
                    f"<g>Pusher</g>：群聊推送任务对象：{id}，推送完成")
        except Exception as e:
            raise e
        try:
            if private_subscriber:
                logger.opt(colors=True).info(
                    # 应为private_target
                    f"<g>Pusher</g>：开始私聊订阅消息推送，对象：{private_target}")
                await private_msg_pusher(msg, private_target)
            else:
                logger.opt(colors=True).info(
                    "<y>Pusher</y>：没有私聊订阅者，跳过私聊推送")
        except Exception as e:
            raise e

    # 更新推送状态
    async def _change_send_status(self):
        if not self.data_id:
            raise AppError.Exception(
                AppError.ParamNotFound, "<r>Pusher</r>：意外的ID缺失！当前id数据不应为空！")
        if not self.source:
            raise AppError.Exception(
                AppError.ParamNotFound, "<r>Pusher</r>：意外的数据源缺失！当前数据源不应为空！")
        if not isinstance(self.source, DatabaseTables.TableName):
            raise AppError.Exception(
                AppError.UnSupportedType, f"<r>Pusher</r>：意外的数据源类型！当前数据源类型不受支持：{type(self.source)}")
        await GeneralDatabaseOperate.update_data(self.conn,
                                                 self.source,
                                                 {"send_status": 1},
                                                 {"id": self.data_id}
                                                 )
        logger.opt(colors=True).info("Pusher：<g>推送状态更新成功！</g>")

    # 数据处理类
    class DataPicking:
        def __init__(self,
                     source: DatabaseTables.TableName,
                     source_db_data: dict[str, Any],
                     anime_db_data: dict[str, Any] | None,
                     target: tuple = ()):
            self.source = source
            self.source_db_data = source_db_data
            self.anime_db_data = anime_db_data
            self.target = target

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
                logger.opt(colors=True).info(
                    f"Pusher：<y>未获取到{self.source.value}内的title！</y>")
                return None

        def _pick_episode(self) -> str | None:
            # 初始化
            season = None
            episode = None
            # 判断
            if self.source == DatabaseTables.TableName.ANI_RSS:
                season = self.source_db_data.get("season")
                episode = self.source_db_data.get('episode')
            elif self.source == DatabaseTables.TableName.EMBY:
                type_ = self.source_db_data.get('type')
                if not type_:
                    logger.opt(colors=True).warning(
                        f"Pusher：<y>意外的没有获取到{self.source.value}的数据类型！</y>\n {self.source_db_data}")
                elif type_ == 'Series':
                    merged_episode = self.source_db_data.get('merged_episode')
                    if merged_episode:
                        return f"多集更新，共更新了{merged_episode}集"
                elif type_ == 'Episode':
                    season = self.source_db_data.get('season')
                    episode = self.source_db_data.get('episode')
                else:
                    logger.opt(colors=True).warning(
                        f"Pusher：<y>未定义处理的{self.source.value}的数据类型：{type_}</y>")
            if all([
                season is not None,
                str(season).isdigit(),
                episode is not None,
                str(episode).isdigit(),
            ]):
                # 该断言仅为避免IDE静态类型检查失败
                assert season is not None and episode is not None
                return f"S{int(season):02d}-E{int(episode):02d}"
            else:
                logger.opt(colors=True).info(
                    f"Pusher：<y>获取到{self.source.value}的season和episode数据有误:\n season: {season} episode: {episode}</y>")
                return None

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

        def _pick_timestamp(self) -> str | None:
            if self.source in (DatabaseTables.TableName.ANI_RSS, DatabaseTables.TableName.EMBY):
                timestamp = self.source_db_data.get('timestamp')
                if timestamp:
                    return datetime.fromisoformat(timestamp).strftime('%m-%d %H:%M:%S')
                else:
                    logger.opt(colors=True).info(
                        "Pusher：<y>没有获取到数据时间戳！</y>")
                    return None
            else:
                logger.opt(colors=True).info(
                    f'Pusher：<y>数据源异常！{self.source}</y>')
                return None

        def _pick_source(self) -> str:
            return self.source.value

        def _pick_action(self) -> str | None:
            if self.source == DatabaseTables.TableName.ANI_RSS:
                return self.source_db_data.get('action')
            elif self.source == DatabaseTables.TableName.EMBY:
                return "媒体库更新完成"
            else:
                logger.opt(colors=True).info("Pusher：<y>没有获取到推送类型！</y>")
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
                logger.opt(colors=True).info('Pusher：<y>未获取到评分信息！</y>')
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
            self.target为(group_target, private_target)元组
            group_target: list[str] 群组推送目标
            private_target: list[str] 私聊推送目标

            group_subscriber: dict[str, list[str]] 群组推送目标订阅者
            private_subscriber: list[str] 私聊推送目标订阅者
            '''
            # 参数合规性检查
            if not self.anime_db_data:
                logger.opt(colors=True).info(
                    "<y>Pusher</y>：未获取到Anime数据库数据！无法获取推送目标！")
                return ({}, [])
            if len(self.target) != 2:
                raise AppError.Exception(
                    AppError.InvalidLength, "<y>Pusher</y>：错误的推送目标结构！")
            # 配置推送目标
            group_target = self.target[0]
            private_target = self.target[1]
            # 读取数据库json配置
            txt_group_subscriber = self.anime_db_data.get("group_subscriber")
            txt_private_subscriber = self.anime_db_data.get(
                "private_subscriber")
            # 处理 group_subscriber（字典或 None）
            json_group_subscriber = {}  # 默认空对象
            if txt_group_subscriber is not None:
                try:
                    json_group_subscriber = json.loads(txt_group_subscriber)
                except (TypeError, ValueError) as e:
                    logger.opt(colors=True).warning(
                        f"<y>Pusher</y>：group_subscriber 结构异常，无法读取：{e}")
                    pass  # 保持默认 {}
            # 处理 private_subscriber（列表或 None）
            json_private_subscriber = []  # 默认空数组
            if txt_private_subscriber is not None:
                try:
                    json_private_subscriber = json.loads(
                        txt_private_subscriber)
                except (TypeError, ValueError) as e:
                    logger.opt(colors=True).warning(
                        f"<y>Pusher</y>：private_subscriber 结构异常，无法读取：{e}")
                    pass  # 保持默认 []
            # 获取实际可用订阅用户
            private_subscriber = list(
                set(json_private_subscriber) & set(private_target))
            group_subscriber = {
                group: users
                for group, users in json_group_subscriber.items()
                if group in group_target
            }
            return (group_subscriber, private_subscriber)

        def _pick_image_queue(self) -> list:
            # 初始化图片优先级队列
            img_queue = []
            if self.anime_db_data:
                img_queue.append(self.anime_db_data.get(
                    "emby_series_tag", None))
            if self.source == DatabaseTables.TableName.EMBY:
                img_queue.append(self.source_db_data.get(
                    "series_tag", None))
            if self.anime_db_data:
                img_queue.append(self.anime_db_data.get(
                    "ani_rss_image", None))
            if self.source == DatabaseTables.TableName.ANI_RSS:
                img_queue.append(
                    self.source_db_data.get("image_url", None))
            filtered_queue = [
                x for x in img_queue if x is not None and x.strip() != ""]
            cleaned_queue = list(dict.fromkeys(filtered_queue))
            return cleaned_queue

        def _pick_series_id(self) -> str | None:
            if self.source == DatabaseTables.TableName.EMBY:
                return str(self.source_db_data["series_id"]) if self.source_db_data.get("series_id") else None
            else:
                return None

    # 处理图片队列
    class ImageQueueProcess:
        def __init__(self, image_queue: list, series_id: str | None = None) -> None:
            self.series_id = series_id
            self.img_queue = image_queue
            self.placeholder_path = Path(__file__).resolve(
            ).parents[2] / "others" / "placeholder_image.jpg"

        async def process(self) -> list:
            processed_list = []

            for item in self.img_queue:
                try:
                    if PublicUtils.is_valid_url(item):
                        path = await self._process_ANI_RSS_item(item)
                    else:
                        path = await self._process_emby_item(item)
                    processed_list.append(path)
                except Exception as e:
                    logger.opt(colors=True).error(
                        f"<r>Pusher</r>：处理图片时出错: {str(e)}")
                    continue
            unique_list = list(dict.fromkeys(processed_list))
            if not unique_list:
                logger.opt(colors=True).warning(
                    "<y>Pusher</y>：处理图片队列后未获取到有效图片，使用占位图片！")
                unique_list.append(self.placeholder_path)
            logger.opt(colors=True).info(
                f"<y>Pusher</y>：已处理图片队列：{unique_list}")
            return unique_list

        # 处理AniRSS图片
        async def _process_ANI_RSS_item(self, item: str) -> Path:
            infer_local_path = PublicUtils.infer_image_local_path(
                DatabaseTables.TableName.ANI_RSS, item)
            verifier = ImageVerification(
                DatabaseTables.TableName.ANI_RSS,
                item,
                infer_local_path
            )
            return await verifier.process()

        # 处理Emby图片
        async def _process_emby_item(self, item: str) -> Path:
            """处理Emby标签类型的图片项"""
            # 推测本地图片地址
            infer_local_path = PublicUtils.infer_image_local_path(
                DatabaseTables.TableName.EMBY, item
            )
            # 如果Emby功能未启用则，判断本地图片是否存在如果存在则使用，否则使用占位图片
            if not FUNCTION.emby_enabled:
                if infer_local_path.is_file():
                    return infer_local_path
                return self.placeholder_path
            # 如果Emby功能已启用且获取到series_id则拼接url验证Emby图片
            if not self.series_id:
                logger.opt(colors=True).warning(
                    "<y>Pusher</y>：Emby功能已启用，但未获取到series_id，将使用占位图片！"
                )
                return self.placeholder_path
            url = PublicUtils.get_emby_image_url(
                APPCONFIG.emby_host, self.series_id, item
            )
            verifier = ImageVerification(
                DatabaseTables.TableName.EMBY, url, infer_local_path
            )
            return await verifier.process()
