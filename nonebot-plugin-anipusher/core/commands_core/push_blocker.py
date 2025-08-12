from nonebot import on_command, logger
from nonebot.exception import FinishedException
from ...config import PUSHTARGET, JsonStorage

temp_block_push = on_command(
    "屏蔽推送"
)

restart_push = on_command(
    "重启推送"
)


@temp_block_push.handle()
async def temp_block_push_handle():
    logger.opt(colors=True).info("匹配命令：<g>屏蔽推送</g>")
    try:
        # 保存当前用户的推送目标
        push_target = {
            "PrivatePushTarget": PUSHTARGET.PrivatePushTarget,
            "GroupPushTarget": PUSHTARGET.GroupPushTarget
        }
        await JsonStorage.write(push_target)
        # 清空当前用户的推送目标
        PUSHTARGET.PrivatePushTarget.clear()
        PUSHTARGET.GroupPushTarget.clear()
        logger.opt(colors=True).info("推送已屏蔽")
        await temp_block_push.finish("推送已暂时屏蔽，期间消息不再补发，如需恢复推送。请使用命令：重启推送")
    except FinishedException:
        # 直接忽略FinishedException
        pass
    except Exception as e:
        logger.opt(colors=True).error(f"屏蔽推送异常：<r>{str(e)}</r>")
        await temp_block_push.finish(f"屏蔽推送失败，请检查日志{e}")


@restart_push.handle()
async def restart_push_handle():
    logger.opt(colors=True).info("匹配命令：<g>重启推送</g>")
    try:
        # 恢复之前保存的推送目标
        push_target = await JsonStorage.read()
        PUSHTARGET.PrivatePushTarget = push_target.get("PrivatePushTarget", {})
        PUSHTARGET.GroupPushTarget = push_target.get("GroupPushTarget", {})
        await restart_push.finish("推送已恢复")
    except FinishedException:
        # 直接忽略FinishedException
        pass
    except Exception as e:
        logger.opt(colors=True).error(f"重启推送异常：<r>{str(e)}</r>")
        await restart_push.finish(f"重启推送失败，请检查日志{e}")
