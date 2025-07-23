
from nonebot import on_command, logger
from nonebot.exception import FinishedException
from pathlib import Path

from ...config import PUSHTARGET, JsonIO

show_push_target = on_command(
    "查看推送目标"
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
