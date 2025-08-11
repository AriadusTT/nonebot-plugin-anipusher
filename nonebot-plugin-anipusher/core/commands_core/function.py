from nonebot.exception import FinishedException
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, GroupMessageEvent
from ...config import PUSHTARGET, JsonStorage
from ...database import DatabaseTables


register_emby_push = on_command(
    "注册Emby推送", aliases={"注册Emby推送服务", "注册Emby推送功能", "注册Emby推送功能服务", "启用Emby推送"})

register_anirss_push = on_command(
    "注册AniRSS推送", aliases={"注册AniRSS推送服务", "注册AniRSS推送功能", "注册AniRSS推送功能服务", "启用AniRSS推送"})

unregister_emby_push = on_command(
    "取消Emby推送", aliases={"取消Emby推送服务", "取消Emby推送功能", "取消Emby推送功能服务", "禁用Emby推送"})

unregister_anirss_push = on_command(
    "取消AniRSS推送", aliases={"取消AniRSS推送服务", "取消AniRSS推送功能", "取消AniRSS推送功能服务", "禁用AniRSS推送"})


@register_emby_push.handle()
async def register_emby(event: PrivateMessageEvent | GroupMessageEvent) -> None:
    logger.opt(colors=True).info("匹配命令：<g>注册Emby推送</g>")
    try:
        # 如果是私聊消息
        if isinstance(event, PrivateMessageEvent):
            user_id = int(event.user_id)
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
            # 添加用户到推送目标
            private_target.append(user_id)
            await JsonStorage.update(
                {"PrivatePushTarget": {
                    DatabaseTables.TableName.EMBY.value: private_target}})
            logger.opt(colors=True).info(
                "Register：<g>注册成功</g>")
            await register_emby_push.finish("注册成功！请注意，私聊推送仅推送订阅过的内容更新。")
        elif isinstance(event, GroupMessageEvent):
            group_id = int(event.group_id)
            if not group_id or not isinstance(group_id, int):
                logger.opt(colors=True).error(
                    "Register：<r>无法获取群组ID或ID格式错误</r>")
                await register_emby_push.finish("Error：无法获取群组ID或ID格式错误")
            # 获取当前用户推送目标
            group_target = PUSHTARGET.GroupPushTarget.setdefault(
                DatabaseTables.TableName.EMBY.value, [])
            if group_id in group_target:
                logger.opt(colors=True).info(
                    "Register：<y>群组已注册,无需重复注册</y>")
                await register_emby_push.finish("群组已注册,无需重复注册")
            group_target.append(group_id)
            await JsonStorage.update(
                {"GroupPushTarget": {
                    DatabaseTables.TableName.EMBY.value: group_target}})
            logger.opt(colors=True).info(
                "Register：<g>注册成功</g>")
            await register_emby_push.finish("注册成功！新内容消息将推送至本群组。")
    except FinishedException:
        # 直接忽略FinishedException
        pass
    except Exception as e:
        logger.opt(colors=True).error(f"Register：<r>{str(e)}</r>")
        await register_emby_push.finish(f"Error：{str(e)}")


@register_anirss_push.handle()
async def register_anirss(event: PrivateMessageEvent | GroupMessageEvent) -> None:
    logger.opt(colors=True).info("匹配命令：<g>注册AniRSS推送</g>")
    try:
        # 如果是私聊消息
        if isinstance(event, PrivateMessageEvent):
            user_id = int(event.user_id)
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
            # 添加用户到推送目标
            private_target.append(user_id)
            await JsonStorage.update(
                {"PrivatePushTarget": {
                    DatabaseTables.TableName.ANI_RSS.value: private_target}})
            logger.opt(colors=True).info(
                "Register：<g>注册成功</g>")
            await register_anirss_push.finish("注册成功！请注意，私聊推送仅推送订阅过的内容更新。")
        elif isinstance(event, GroupMessageEvent):
            group_id = int(event.group_id)
            if not group_id or not isinstance(group_id, int):
                logger.opt(colors=True).error(
                    "Register：<r>无法获取群组ID或ID格式错误</r>")
                await register_anirss_push.finish("Error：无法获取群组ID或ID格式错误")
            # 获取当前用户推送目标
            group_target = PUSHTARGET.GroupPushTarget.setdefault(
                DatabaseTables.TableName.ANI_RSS.value, [])
            if group_id in group_target:
                logger.opt(colors=True).info(
                    "Register：<y>群组已注册,无需重复注册</y>")
                await register_anirss_push.finish("群组已注册,无需重复注册")
            group_target.append(group_id)
            await JsonStorage.update(
                {"GroupPushTarget": {
                    DatabaseTables.TableName.ANI_RSS.value: group_target}})
            logger.opt(colors=True).info(
                "Register：<g>注册成功</g>")
            await register_anirss_push.finish("注册成功！新内容消息将推送至本群组。")
    except FinishedException:
        # 直接忽略FinishedException
        pass
    except Exception as e:
        logger.opt(colors=True).error(f"Register：<r>{str(e)}</r>")
        await register_anirss_push.finish(f"Error：{str(e)}")


@unregister_emby_push.handle()
async def unregister_emby(event: PrivateMessageEvent | GroupMessageEvent) -> None:
    logger.opt(colors=True).info("匹配命令：<g>注销Emby推送</g>")
    try:
        # 如果是私聊消息
        if isinstance(event, PrivateMessageEvent):
            user_id = int(event.user_id)
            if not user_id or not isinstance(user_id, int):
                logger.opt(colors=True).error(
                    "Register：<r>无法获取用户ID或ID格式错误</r>")
                await unregister_emby_push.finish("Error：无法获取用户ID或ID格式错误")
            # 获取当前用户推送目标
            private_target = PUSHTARGET.PrivatePushTarget.setdefault(
                DatabaseTables.TableName.EMBY.value, [])
            if user_id not in private_target:
                logger.opt(colors=True).info(
                    "Register：<y>用户未注册,无需注销推送</y>")
                await unregister_emby_push.finish("用户未注册,无需注销推送")
            # 移除用户
            private_target.remove(user_id)
            await JsonStorage.update(
                {"PrivatePushTarget": {
                    DatabaseTables.TableName.EMBY.value: private_target}})
            logger.opt(colors=True).info(
                "Register：<g>注销EMBY推送服务成功！</g>")
            await unregister_emby_push.finish("注销EMBY推送服务成功！")
        elif isinstance(event, GroupMessageEvent):
            group_id = int(event.group_id)
            if not group_id or not isinstance(group_id, int):
                logger.opt(colors=True).error(
                    "Register：<r>无法获取群组ID或ID格式错误</r>")
                await unregister_emby_push.finish("Error：无法获取群组ID或ID格式错误")
            # 获取当前用户推送目标
            group_target = PUSHTARGET.GroupPushTarget.setdefault(
                DatabaseTables.TableName.EMBY.value, [])
            if group_id not in group_target:
                logger.opt(colors=True).info(
                    "Register：<y>群组未注册,无需注销推送</y>")
                await unregister_emby_push.finish("群组未注册,无需注销推送")
            # 移除群组
            group_target.remove(group_id)
            await JsonStorage.update(
                {"GroupPushTarget": {
                    DatabaseTables.TableName.EMBY.value: group_target}})
            logger.opt(colors=True).info(
                "Register：<g>注销EMBY推送服务成功！</g>")
            await unregister_emby_push.finish("注销EMBY推送服务成功！")
    except FinishedException:
        # 直接忽略FinishedException
        pass
    except Exception as e:
        logger.opt(colors=True).error(f"Register：<r>{str(e)}</r>")
        await unregister_emby_push.finish(f"Error：{str(e)}")


@unregister_anirss_push.handle()
async def unregister_anirss(event: PrivateMessageEvent | GroupMessageEvent) -> None:
    logger.opt(colors=True).info("匹配命令：<g>注销AniRSS推送</g>")
    try:
        # 如果是私聊消息
        if isinstance(event, PrivateMessageEvent):
            user_id = int(event.user_id)
            if not user_id or not isinstance(user_id, int):
                logger.opt(colors=True).error(
                    "Register：<r>无法获取用户ID或ID格式错误</r>")
                await unregister_anirss_push.finish("Error：无法获取用户ID或ID格式错误")
            # 获取当前用户推送目标
            private_target = PUSHTARGET.PrivatePushTarget.setdefault(
                DatabaseTables.TableName.ANI_RSS.value, [])
            if user_id not in private_target:
                logger.opt(colors=True).info(
                    "Register：<y>用户未注册,无需注销推送</y>")
                await unregister_anirss_push.finish("用户未注册,无需注销推送")
            # 移除用户
            private_target.remove(user_id)
            await JsonStorage.update(
                {"PrivatePushTarget": {
                    DatabaseTables.TableName.ANI_RSS.value: private_target
                }}
            )
            logger.opt(colors=True).info(
                "Register：<g>注销ANIRSS推送服务成功！</g>")
            await unregister_anirss_push.finish("注销ANIRSS推送服务成功！")
        elif isinstance(event, GroupMessageEvent):
            group_id = int(event.group_id)
            if not group_id or not isinstance(group_id, int):
                logger.opt(colors=True).error(
                    "Register：<r>无法获取群组ID或ID格式错误</r>")
                await unregister_anirss_push.finish("Error：无法获取群组ID或ID格式错误")
            # 获取当前用户推送目标
            group_target = PUSHTARGET.GroupPushTarget.setdefault(
                DatabaseTables.TableName.ANI_RSS.value, [])
            if group_id not in group_target:
                logger.opt(colors=True).info(
                    "Register：<y>群组未注册,无需注销推送</y>")
                await unregister_anirss_push.finish("群组未注册,无需注销推送")
            # 移除群组
            group_target.remove(group_id)
            await JsonStorage.update(
                {"GroupPushTarget": {
                    DatabaseTables.TableName.ANI_RSS.value: group_target
                }}
            )
            logger.opt(colors=True).info(
                "Register：<g>注销ANIRSS推送服务成功！</g>")
            await unregister_anirss_push.finish("注销ANIRSS推送服务成功！")
    except FinishedException:
        # 直接忽略FinishedException
        pass
    except Exception as e:
        logger.opt(colors=True).error(f"Register：<r>{str(e)}</r>")
        await unregister_anirss_push.finish(f"Error：{str(e)}")
