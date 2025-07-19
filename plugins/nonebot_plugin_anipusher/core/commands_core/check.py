
import re
from nonebot import on_command, logger
from nonebot.exception import FinishedException
from pathlib import Path

from ...config import PUSHTARGET, JsonIO

show_push_target = on_command(
    "查看推送目标"
)

temp_block_push = on_command(
    "屏蔽推送"
)

restart_push = on_command(
    "重启推送"
)

TARGET_PATH = Path(__file__).resolve().parents[2] / "target.json"


@show_push_target.handle()
async def show_push_target_handle():
    logger.opt(colors=True).info("匹配命令：<g>查看推送目标</g>")
    try:
        # 获取当前用户推送目标
        def format_targets(targets):
            return "\n".join([f"{k}: {v}" for k, v in targets])
        private_target = PUSHTARGET.PrivatePushTarget.items()
        group_target = PUSHTARGET.GroupPushTarget.items()
        await show_push_target.finish(
            f"当前推送目标：\n私聊推送：\n{format_targets(private_target)}"
            f"\n群组推送：\n{format_targets(group_target)}"
        )
    except FinishedException:
        # 直接忽略FinishedException
        pass
    except Exception as e:
        logger.opt(colors=True).error(f"查看推送目标异常：<r>{str(e)}</r>")


@temp_block_push.handle()
async def temp_block_push_handle():
    logger.opt(colors=True).info("匹配命令：<g>屏蔽推送</g>")
    try:
        # 保存当前用户的推送目标
        push_target = {
            "PrivatePushTarget": PUSHTARGET.PrivatePushTarget,
            "GroupPushTarget": PUSHTARGET.GroupPushTarget
        }
        JsonIO.update_json(TARGET_PATH, push_target)
        # 清空当前用户的推送目标
        PUSHTARGET.PrivatePushTarget.clear()
        PUSHTARGET.GroupPushTarget.clear()
        await temp_block_push.finish("推送已屏蔽")
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
        push_target = JsonIO.read_json(TARGET_PATH)
        PUSHTARGET.PrivatePushTarget = push_target.get("PrivatePushTarget", {})
        PUSHTARGET.GroupPushTarget = push_target.get("GroupPushTarget", {})
        await restart_push.finish("推送已恢复")
    except FinishedException:
        # 直接忽略FinishedException
        pass
    except Exception as e:
        logger.opt(colors=True).error(f"重启推送异常：<r>{str(e)}</r>")
        await restart_push.finish(f"重启推送失败，请检查日志{e}")
