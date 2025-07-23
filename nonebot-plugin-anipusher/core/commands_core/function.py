from nonebot import on_command, logger
from nonebot.exception import FinishedException
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, GroupMessageEvent
from pathlib import Path
from ...database import DatabaseTables
from ...config import PUSHTARGET, JsonIO

TARGET_PATH = Path(__file__).resolve().parents[2] / "target.json"
register_emby_push = on_command(
    "注册Emby推送", aliases={"注册Emby推送服务", "注册Emby推送功能", "注册Emby推送功能服务", "启用Emby推送"})

register_anirss_push = on_command(
    "注册AniRSS推送", aliases={"注册AniRSS推送服务", "注册AniRSS推送功能", "注册AniRSS推送功能服务", "启用AniRSS推送"})

unregister_emby_push = on_command(
    "取消Emby推送", aliases={"取消Emby推送服务", "取消Emby推送功能", "取消Emby推送功能服务", "禁用Emby推送"})

unregister_anirss_push = on_command(
    "取消AniRSS推送", aliases={"取消AniRSS推送服务", "取消AniRSS推送功能", "取消AniRSS推送功能服务", "禁用AniRSS推送"})

temp_block_push = on_command(
    "屏蔽推送"
)

restart_push = on_command(
    "重启推送"
)


@register_emby_push.handle()
async def register_emby(event: PrivateMessageEvent | GroupMessageEvent):
    logger.opt(colors=True).info("匹配命令：<g>注册Emby推送</g>")
    try:
        # 如果是私聊消息
        if isinstance(event, PrivateMessageEvent):
            user_id = int(event.user_id)
            # 验证用户id
            if not user_id or not isinstance(user_id, int):
                logger.opt(colors=True).error(
                    "Register：<r>无法获取用户ID或ID格式错误</r>")
                await register_emby_push.finish("Error：无法获取用户ID或ID格式错误")
            # 获取当前用户推送目标
            private_target = PUSHTARGET.PrivatePushTarget.setdefault(
                DatabaseTables.TableName.EMBY.value, [])
            if user_id in private_target:
                logger.opt(colors=True).info(
                    "Register：<y>用户已注册,无需重复注册</y>")
                await register_emby_push.finish("用户已注册,无需重复注册")
            # 添加当前用户推送目标
            private_target.append(user_id)
            # 持久化
            JsonIO.update_json(
                TARGET_PATH, {"PrivatePushTarget": {
                    DatabaseTables.TableName.EMBY.value: private_target}})
            logger.opt(colors=True).info(
                "Register：<g>注册成功！</g>")
            await register_emby_push.finish("注册成功！")
        if isinstance(event, GroupMessageEvent):
            group_id = int(event.group_id)
            if not group_id or not isinstance(group_id, int):
                logger.opt(colors=True).error(
                    "Register：<r>无法获取群组ID或ID格式错误</r>")
                await register_emby_push.finish("Error：无法获取群组ID或ID格式错误")
            group_target = PUSHTARGET.GroupPushTarget.setdefault(
                DatabaseTables.TableName.EMBY.value, [])
            if group_id in group_target:
                logger.opt(colors=True).info(
                    "Register：<y>群组已注册,无需重复注册</y>")
                await register_emby_push.finish("群组已注册,无需重复注册")
            group_target.append(group_id)
            JsonIO.update_json(
                TARGET_PATH, {"GroupPushTarget": {
                    DatabaseTables.TableName.EMBY.value: group_target}})
            logger.opt(colors=True).info(
                "Register：<g>注册成功！</g>")
            await register_emby_push.finish("注册成功！新内容消息将推送至本群组。")
    except FinishedException:
        # 直接忽略FinishedException
        pass
    except Exception as e:
        logger.opt(colors=True).error(f"Register：<r>{str(e)}</r>")
        await register_emby_push.finish(f"Error：{str(e)}")


@register_anirss_push.handle()
async def register_anirss(event: PrivateMessageEvent | GroupMessageEvent):
    logger.opt(colors=True).info("匹配命令：<g>注册AniRSS推送</g>")
    try:
        # 如果是私聊消息
        if isinstance(event, PrivateMessageEvent):
            user_id = int(event.user_id)
            # 验证用户id
            if not user_id or not isinstance(user_id, int):
                logger.opt(colors=True).error(
                    "Register：<r>无法获取用户ID或ID格式错误</r>")
                await register_anirss_push.finish("Error：无法获取用户ID或ID格式错误")
            # 获取当前用户推送目标
            private_target = PUSHTARGET.PrivatePushTarget.setdefault(
                DatabaseTables.TableName.ANI_RSS.value, [])
            if user_id in private_target:
                logger.opt(colors=True).info(
                    "Register：<y>用户已注册,无需重复注册</y>")
                await register_anirss_push.finish("用户已注册,无需重复注册")
            # 添加当前用户推送目标
            private_target.append(user_id)
            # 持久化
            JsonIO.update_json(
                TARGET_PATH, {"PrivatePushTarget": {
                    DatabaseTables.TableName.ANI_RSS.value: private_target}})
            logger.opt(colors=True).info(
                "Register：<g>注册成功！</g>")
            await register_anirss_push.finish("注册成功！")
        if isinstance(event, GroupMessageEvent):
            group_id = int(event.group_id)
            if not group_id or not isinstance(group_id, int):
                logger.opt(colors=True).error(
                    "Register：<r>无法获取群组ID或ID格式错误</r>")
                await register_anirss_push.finish("Error：无法获取群组ID或ID格式错误")
            group_target = PUSHTARGET.GroupPushTarget.setdefault(
                DatabaseTables.TableName.ANI_RSS.value, [])
            if group_id in group_target:
                logger.opt(colors=True).info(
                    "Register：<y>群组已注册,无需重复注册</y>")
                await register_anirss_push.finish("群组已注册,无需重复注册")
            group_target.append(group_id)
            JsonIO.update_json(
                TARGET_PATH, {"GroupPushTarget": {
                    DatabaseTables.TableName.ANI_RSS.value: group_target}})
            logger.opt(colors=True).info(
                "Register：<g>注册成功！</g>")
            await register_anirss_push.finish("注册成功！新内容消息将推送至本群组。")
    except FinishedException:
        # 直接忽略FinishedException
        pass
    except Exception as e:
        logger.opt(colors=True).error(f"Register：<r>{str(e)}</r>")
        await register_anirss_push.finish(f"Error：{str(e)}")


@unregister_emby_push.handle()
async def unregister_emby(event: PrivateMessageEvent | GroupMessageEvent):
    logger.opt(colors=True).info("匹配命令：<g>注销Emby推送</g>")
    try:
        # 如果是私聊消息
        if isinstance(event, PrivateMessageEvent):
            user_id = int(event.user_id)
            # 验证用户id
            if not user_id or not isinstance(user_id, int):
                logger.opt(colors=True).error(
                    "Register：<r>无法获取用户ID或ID格式错误</r>")
                await unregister_emby_push.finish("Error：无法获取用户ID或ID格式错误")
            # 获取当前用户推送目标
            private_target = PUSHTARGET.PrivatePushTarget.setdefault(
                DatabaseTables.TableName.EMBY.value, [])
            if user_id not in private_target:
                logger.opt(colors=True).info(
                    "Register：<y>用户未注册,无法注销</y>")
                await unregister_emby_push.finish("用户未注册,无法注销")
            # 移除当前用户推送目标
            private_target.remove(user_id)
            # 持久化
            JsonIO.update_json(
                TARGET_PATH, {"PrivatePushTarget": {
                    DatabaseTables.TableName.EMBY.value: private_target}})
            logger.opt(colors=True).info(
                "Register：<g>注销成功！</g>")
            await unregister_emby_push.finish("注销成功！新消息将不再推送给您。")
        if isinstance(event, GroupMessageEvent):
            group_id = int(event.group_id)
            if not group_id or not isinstance(group_id, int):
                logger.opt(colors=True).error(
                    "Register：<r>无法获取群组ID或ID格式错误</r>")
                await unregister_emby_push.finish("Error：无法获取群组ID或ID格式错误")
            group_target = PUSHTARGET.GroupPushTarget.setdefault(
                DatabaseTables.TableName.EMBY.value, [])
            if group_id not in group_target:
                logger.opt(colors=True).info(
                    "Register：<y>群组未注册,无法注销</y>")
                await unregister_emby_push.finish("群组未注册,无法注销")
            group_target.remove(group_id)
            JsonIO.update_json(
                TARGET_PATH, {"GroupPushTarget": {
                    DatabaseTables.TableName.EMBY.value: group_target}})
            logger.opt(colors=True).info(
                "Register：<g>注销成功！</g>")
            await unregister_emby_push.finish("注销成功！新消息将不再推送给本群组。")
    except FinishedException:
        # 直接忽略FinishedException
        pass
    except Exception as e:
        logger.opt(colors=True).error(f"Register：<r>{str(e)}</r>")
        await unregister_emby_push.finish(f"Error：{str(e)}")


@unregister_anirss_push.handle()
async def unregister_anirss(event: PrivateMessageEvent | GroupMessageEvent):
    logger.opt(colors=True).info("匹配命令：<g>注销AniRSS推送</g>")
    try:
        # 如果是私聊消息
        if isinstance(event, PrivateMessageEvent):
            user_id = int(event.user_id)
            # 验证用户id
            if not user_id or not isinstance(user_id, int):
                logger.opt(colors=True).error(
                    "Register：<r>无法获取用户ID或ID格式错误</r>")
                await unregister_anirss_push.finish("Error：无法获取用户ID或ID格式错误")
            # 获取当前用户推送目标
            private_target = PUSHTARGET.PrivatePushTarget.setdefault(
                DatabaseTables.TableName.ANI_RSS.value, [])
            if user_id not in private_target:
                logger.opt(colors=True).info(
                    "Register：<y>用户未注册,无法注销</y>")
                await unregister_anirss_push.finish("用户未注册,无法注销")
            # 移除当前用户推送目标
            private_target.remove(user_id)
            # 持久化
            JsonIO.update_json(
                TARGET_PATH, {"PrivatePushTarget": {
                    DatabaseTables.TableName.ANI_RSS.value: private_target}})
            logger.opt(colors=True).info(
                "Register：<g>注销成功！</g>")
            await unregister_anirss_push.finish("注销成功！新消息将不再推送给您。")
        if isinstance(event, GroupMessageEvent):
            group_id = int(event.group_id)
            if not group_id or not isinstance(group_id, int):
                logger.opt(colors=True).error(
                    "Register：<r>无法获取群组ID或ID格式错误</r>")
                await unregister_anirss_push.finish("Error：无法获取群组ID或ID格式错误")
            group_target = PUSHTARGET.GroupPushTarget.setdefault(
                DatabaseTables.TableName.ANI_RSS.value, [])
            if group_id not in group_target:
                logger.opt(colors=True).info(
                    "Register：<y>群组未注册,无法注销</y>")
                await unregister_anirss_push.finish("群组未注册,无法注销")
            group_target.remove(group_id)
            JsonIO.update_json(
                TARGET_PATH, {"GroupPushTarget": {
                    DatabaseTables.TableName.ANI_RSS.value: group_target}})
            logger.opt(colors=True).info(
                "Register：<g>注销成功！</g>")
            await unregister_anirss_push.finish("注销成功！新消息将不再推送给本群组。")
    except FinishedException:
        # 直接忽略FinishedException
        pass
    except Exception as e:
        logger.opt(colors=True).error(f"Register：<r>{str(e)}</r>")
        await unregister_anirss_push.finish(f"Error：{str(e)}")


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
