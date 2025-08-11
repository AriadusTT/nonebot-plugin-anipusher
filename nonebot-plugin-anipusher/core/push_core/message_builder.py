from typing import Dict, List
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from ...utils import CommonUtils

from nonebot import logger


class MessageBuilder:
    def __init__(self, message_template):
        self.message_template = message_template
        self.data = {}

    def set_data(self, data: Dict[str, str]) -> 'MessageBuilder':
        """设置模板数据"""
        self.data = data
        return self

    def build(self):
        """构建消息段列表"""
        message = Message()
        for text, key in self.message_template:
            if key is None:
                message.append(MessageSegment.text(text + "\n"))
                continue
            if key not in self.data or self.data[key] is None:
                # 跳过缺失或为None的字段
                continue
            if key == "img" or key == "image":
                data = CommonUtils.img_to_base64(self.data[key])
                message.append(MessageSegment.image(data))
                continue
            if key == "at":
                continue  # 处理通用数据时跳过，@消息段需要单独处理
            try:
                formatted_text = text.format(**self.data)
                message.append(MessageSegment.text(formatted_text + "\n"))
            except KeyError:
                pass
        if message and str(message).endswith("\n"):
            message = Message(str(message).rstrip("\n"))
        return message

    @staticmethod
    def append_at(message_segments: List[MessageSegment], subscriber_id: list) -> List[MessageSegment]:
        """追加@消息段"""
        if subscriber_id:
            message_segments.append(MessageSegment.text("订阅提醒："))
            for id in subscriber_id:
                message_segments.append(MessageSegment.at(id))
        return message_segments
