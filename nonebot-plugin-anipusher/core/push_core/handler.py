
from nonebot import logger
from ...database import DatabaseTables, DatabaseService
from ...exceptions import AppError
from .image_service import ImageProcessor
from .data_service import DataPicking
from ...config import PUSHTARGET
from .message_builder import MessageBuilder
from .message_template import MessageTemplate
from .msg_pusher import group_msg_pusher, private_msg_pusher
from ...utils import CommonUtils


class PushService:
    def __init__(self, source: DatabaseTables.TableName):
        self.source = source  # 数据源
        self.tmdb_id = None  # 数据库中未发送数据的TMDBID用于获取Anime库中的数据
        self.id = None  # 数据库中未发送数据的ID,用于最后修改发送状态
        self.private_targets = getattr(PUSHTARGET, "PrivatePushTarget", {}).get(
            getattr(self.source, "value", ""), [])  # 私聊推送目标
        self.group_targets = getattr(PUSHTARGET, "GroupPushTarget", {}).get(
            getattr(self.source, "value", ""), [])  # 群聊推送目标
        self.data_id = None  # 数据库中未发送数据的ID,用于最后修改发送状态
        self.subscribers = ({}, [])  # 订阅者

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
            logger.opt(colors=True).info(
                f"<g>Pusher</g>：{self.source.value} 获取未发送数据 <g>成功</g>")
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
        anime_data = await self._get_data_from_anime_db()
        # 将获取到的数据汇总，筛选出推送数据
        picked_data, hybrid_image_queue, series_id = await self._data_pick(source_data, anime_data)
        # 对混合图片进行处理,获取图片数据
        img_path = await ImageProcessor(hybrid_image_queue, series_id, self.tmdb_id).process()
        # 将图片路径添加到推送数据中
        picked_data["image"] = img_path
        # 推送
        await self._push(picked_data)
        logger.opt(colors=True).info(
            f"<g>Pusher</g>：源：{self.source.value}，TMDB ID：{self.tmdb_id}，消息推送 <g>完成</g>")
        # 更新数据库
        await self._modify_send_status()
        logger.opt(colors=True).info(
            "<g>Pusher</g>：数据库发送状态更新 <g>完成</g>")
        logger.opt(colors=True).info(f"<g>Pusher</g>：{self.tmdb_id} 推送服务 <g>结束</g> ")
        return

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

    async def _get_data_from_anime_db(self):
        # 判断是否有TMDB ID，没有则直接返回默认模板
        if not self.tmdb_id:
            logger.opt(colors=True).warning(
                f"<y>Pusher</y>：{self.source.value} 未配置TMDB ID")
            return DatabaseTables.get_table_schema(
                DatabaseTables.TableName.ANIME).copy()
        # 通过TMDB ID获取Anime库中的数据，没有则返回默认模板
        try:
            anime_db_data = await self._search_in_animedb_by_tmdbid()
            if isinstance(anime_db_data, list) and len(anime_db_data) != 0:
                return await self._convert_first_db_row_to_dict(
                    list(anime_db_data),
                    DatabaseTables.TableName.ANIME)
            else:
                logger.opt(colors=True).warning(
                    f"<y>Pusher</y>：TMDB ID:{self.tmdb_id} 在Anime库中未找到对应条目")
        except Exception as e:
            logger.opt(colors=True).error(
                f"<r>Pusher</r>：{e}")
        return DatabaseTables.get_table_schema(
            DatabaseTables.TableName.ANIME).copy()

    async def _search_in_animedb_by_tmdbid(self):
        try:
            return await DatabaseService.select_data(
                table_name=DatabaseTables.TableName.ANIME,
                where={"tmdb_id": self.tmdb_id},
                order_by="tmdb_id DESC")
        except Exception as e:
            raise e

    async def _data_pick(self, source_data, anime_data):
        if not source_data or not anime_data:
            raise AppError.Exception(AppError.ParamNotFound, "意外的异常，缺少必要的参数")
        picker = DataPicking(self.source, source_data, anime_data)
        self.data_id = picker._pick_id()
        self.subscriber = picker._pick_subscriber()
        hybrid_image_queue = picker._pick_image_queue()
        series_id = picker._pick_series_id()
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
        return picked_data, hybrid_image_queue, series_id

    async def _push(self, picked_data):
        # 构造推送消息器
        try:
            builder = MessageBuilder(MessageTemplate().PushMessage.copy())
            builder.set_data(picked_data)
            message_without_at = builder.build()
        except Exception as e:
            logger.opt(colors=True).error(
                f"<r>Pusher</r>：模板消息填充失败，{e}")
        try:
            # 推送消息群组消息
            await self._group_push(message_without_at)
            # 推送消息私人消息
            await self._private_push(message_without_at)
        except Exception as e:
            logger.opt(colors=True).error(
                f"<r>Pusher</r>：{e}")

    async def _private_push(self, message):
        if not self.private_targets:
            logger.opt(colors=True).info(
                f"<y>Pusher</y>：{self.source.value} 没有需要推送的个人")
            return
        private_subscribers = self.subscriber[1]  # 获取订阅者列表
        target = list(set(str(x) for x in private_subscribers)
                      & set(str(x) for x in self.private_targets))  # 获取交集
        if not target:
            logger.opt(colors=True).info(
                f"<y>Pusher</y>：{self.source.value} 没有用户订阅{self.tmdb_id}并启用私聊推送")
            return
        await private_msg_pusher(message, target)

    async def _group_push(self, message):
        if not self.group_targets:
            logger.opt(colors=True).info(
                f"<y>Pusher</y>：{self.source.value} 没有需要推送的群组")
            return
        group_subscribers = self.subscriber[0]  # 获取订阅者列表
        for group in self.group_targets:
            subscribers = group_subscribers.get(group, [])
            message = MessageBuilder.append_at(message, subscribers)
            await group_msg_pusher(message, [group])

    async def _modify_send_status(self):
        try:
            await DatabaseService.update_data(
                table_name=self.source,
                where={"id": self.data_id},
                update_columns={"send_status": 1})
        except Exception as e:
            logger.opt(colors=True).error(
                f"<r>Pusher</r>：{e}")
