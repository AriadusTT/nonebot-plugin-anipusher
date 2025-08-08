from nonebot import get_bot, logger


async def private_msg_pusher(msg, private_target: list | None):
    """
    向指定用户发送私聊消息。

    Args:
        msg: 要发送的消息内容。
        private_target: 目标用户ID列表，如果为None则不发送。

    Raises:
        Exception: 如果无法获取nonebot对象，抛出异常。
    """
    bot = get_bot()
    if not bot:
        raise Exception('nonebot对象获取失败')
    if private_target:
        for user_id in private_target:
            try:
                await bot.send_private_msg(user_id=user_id, message=msg)
            except Exception as e:
                logger.opt(colors=True).error(
                    f"<r>Pusher</r>：用户 {user_id} 消息发送失败: {e}")


async def group_msg_pusher(msg, group_target: list | None):
    """
    向指定群组发送群聊消息。

    Args:
        msg: 要发送的消息内容。
        group_target: 目标群组ID列表，如果为None则不发送。

    Raises:
        Exception: 如果无法获取nonebot对象，抛出异常。
    """
    bot = get_bot()
    if not bot:
        raise Exception('nonebot对象获取失败')
    if group_target:
        for group_id in group_target:
            try:
                await bot.send_group_msg(group_id=group_id, message=msg)
            except Exception as e:
                logger.opt(colors=True).error(
                    f"<r>Pusher</r>：群组 {group_id} 消息发送失败: {e}")
