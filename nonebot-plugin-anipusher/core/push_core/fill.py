from typing import Sequence
from nonebot.adapters.onebot.v11 import MessageSegment


def fill_message(
    template: Sequence[tuple[str, str | None]],
    fields: dict[str, str] | None = None,
) -> MessageSegment:
    """根据模板和字段生成消息段

    Args:
        template: 消息模板列表，每个元素为 (模板字符串, 字段名或None)
        fields: 包含字段值的字典，默认为None

    Returns:
        MessageSegment: 生成的消息段文本

    Raises:
        ValueError: 当模板格式不正确时
    """
    if fields is None:
        fields = {}

    msg_lines = []

    for line_template, field in template:
        if field is None:
            msg_lines.append(line_template)
        elif field in fields and fields[field] is not None:
            try:
                formatted_line = line_template.format(**fields)
                msg_lines.append(formatted_line)
            except KeyError:
                continue
    if not msg_lines:
        return MessageSegment.text("Error:Empty message")

    return MessageSegment.text("\n".join(msg_lines))


def fill_img(imgurl: str) -> MessageSegment:
    """创建图片消息段

    Args:
        imgurl: 图片URL或本地路径

    Returns:
        MessageSegment: 图片消息段
    """
    return MessageSegment.image(imgurl)


def fill_at(user_id: int) -> MessageSegment:
    """创建@用户消息段

    Args:
        user_id: 要@的用户QQ号

    Returns:
        MessageSegment: @消息段
    """
    return MessageSegment.at(user_id)
