from nonebot_plugin_waiter import prompt, prompt_until
from nonebot import get_driver, on_command, logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message
from ...external import TmdbRequest
from ...config import FUNCTION
from ...constants.error_handling import AppError
from ...database import DatabaseTables,GeneralDatabaseOperate,SQLiteQueryBuilder
driver = get_driver()


subscribe = on_command("订阅", priority=5)


@subscribe.handle()
async def handle_subscribe(
    matcher: Matcher,
    args: Message = CommandArg()
):
    logger.opt(colors=True).info("匹配命令：<g>订阅</g>")
    # 1.检查TMDB功能是否启用
    if not FUNCTION.tmdb_enabled:
        logger.opt(colors=True).warning("<y>订阅</y>: TMDB功能未启用！请检查配置。")
        await subscribe.finish("TMDB功能未启用！订阅功能将无法使用，请检查配置。")
    # 2.检查参数是否为空,如果为空则提示用户输入剧集标题
    title = args.extract_plain_text().strip()
    if not title:
        title = await prompt("请输入想订阅的剧集标题", timeout=60)
    if not title:
        logger.opt(colors=True).warning("<y>订阅</y>: 超时未收到订阅参数，将结束对话")
        await subscribe.finish("超时未收到标题，将退出订阅")
    else:
        logger.opt(colors=True).info(f"<g>订阅</g>: 确认订阅参数: {title}")
    # 3.获取到订阅参数后，向Tmdb发送请求查询剧集信息
    try:
        response = await TmdbRequest.search_by_title(str(title))
    except Exception as e:
        logger.opt(colors=True).error(f"<r>订阅</r>: 获取剧集信息失败: {str(e)}")
        await subscribe.finish(f"获取剧集信息失败: {str(e)}")
    if not response:
        logger.opt(colors=True).error("<r>订阅</r>: 意外错误，返回数据为空")
        await subscribe.finish("意外错误，返回数据为空")
    # 4.将获取到的剧集信息进行处理
    # 4.1 检查返回数据是否符合预期
    try:
        data = TmdbDataProcessing.process_data(response)
    except AppError.Exception as e:
        logger.opt(colors=True).error(f"<r>订阅</r>: 数据处理异常: {str(e)}")
        await subscribe.finish(f"Tmdb数据处理异常: {str(e)}")
    # 4.2根据不同的返回项目数量进行处理
    # 配置total_results为 data中的total_results字段表示总结果数
    total_results = data.get("total_results", 0)
    # 4.2.1 如果没有找到任何结果，直接提示用户
    if total_results == 0:
        logger.opt(colors=True).warning("<y>订阅</y>: 未找到相关剧集")
        await subscribe.finish("未找到相关剧集，请重新尝试")
    # 配置results为data中的results字段表示查询结果的列表
    results = data.get("results", [])
    if not results:
        logger.opt(colors=True).error("<r>订阅</r>: 意外错误，返回数量不为0，但结果为空")
        await subscribe.finish("意外错误，返回数量不为0，但结果为空")
    # 4.2.2 如果找到到一个结果，直接使用该结果配置tmdb_id和item_data
    if total_results == 1:
        item_data = data["results"][0]
        tmdb_id = item_data.get("id")
        if not tmdb_id:
            logger.opt(colors=True).error("<r>订阅</r>: 未找到剧集ID")
            await subscribe.finish("意外错误，未找到剧集ID")
    else:  # 4.2.3 如果找到多个结果，提示用户选择
        logger.opt(colors=True).info(
            f"<g>订阅</g>: 找到{total_results}个结果，组装消息并等待用户选择")
        max_display = 5  # 最多显示前5个结果
        message = TmdbDataProcessing.feedback_message(
            total_results=total_results,
            results=results,
            max_display=max_display
        )
        # 通过prompt_until等待用户输入选择
        selected_id = await prompt_until(
            message,
            lambda msg: (
                msg.extract_plain_text().strip().isdigit()  # 检查是否为纯数字
                and 1 <= int(msg.extract_plain_text()) <= max_display  # 检查范围
            ),
            timeout=30,  # 设置超时时间为30秒
            timeout_prompt="超时未收到选择，将结束对话",
            finish=True,  # 超时或重试次数过多时结束会话
            retry=5,
            retry_prompt=f"输入错误，请输入1到{max_display}之间的数字。剩余重试次数：{{count}}",
            limited_prompt="重试次数过多，将结束对话"
        )
        # 4.2.3.1 处理用户选择的结果
        if not selected_id:
            logger.opt(colors=True).warning("<y>订阅</y>: 用户未选择任何结果，将结束对话")
            return
        selected_index = int(selected_id.extract_plain_text()) - 1
        item_data = results[selected_index]
        tmdb_id = item_data.get("id")
    # 5.检查获取到的剧集ID是否有效
    if not isinstance(tmdb_id, int):
        logger.opt(colors=True).error("<r>订阅</r>: 获取到的剧集ID无效")
        await subscribe.finish("意外错误，获取到的剧集ID无效")
    if not tmdb_id:
        logger.opt(colors=True).error("<r>订阅</r>: 未找到剧集ID")
        await subscribe.finish("意外错误，未找到剧集ID")
    # 6.成功获取到剧集ID后，进行订阅操作
    try:
        pass
    except Exception as e:
        logger.opt(colors=True).error(f"<r>订阅</r>: 订阅操作失败: {str(e)}")
        await subscribe.finish(f"订阅操作失败: {str(e)}")


class TmdbDataProcessing:

    @staticmethod
    def process_data(response: str) -> dict:
        """
        处理Tmdb返回的数据
        :param response: Tmdb返回的剧集信息
        :return:  # 返回处理后的数据字典，包含以下字段：
        - `page`: 当前页码
        - `total_results`: 总结果数
        - `total_pages`: 总页数
        - `results`: 最多总计20条结果的列表
        """
        try:
            import json
            data = json.loads(response)
            if not isinstance(data, dict):
                raise AppError.Exception(
                    AppError.UnSupportedType, "返回数据类型错误！请检查函数方法")
            return data
        except json.JSONDecodeError as e:
            raise AppError.Exception(
                AppError.UnknownError, f"JSON解析错误: {str(e)}")
        except Exception as e:
            raise AppError.Exception(
                AppError.UnknownError, f"发生未知错误: {str(e)}")

    @staticmethod
    def feedback_message(
            total_results: int,
            results: list,
            max_display: int = 5,
    ) -> str:
        """
        组装反馈消息
        :param page: 当前页码
        :param total_page: 总页数
        :param total_results: 总结果数
        :param results: 结果列表
        :return: 格式化后的消息字符串
        """
        displayed_results = results[:max_display]  # 只取前5项
        message = (
            f"共找到 {total_results} 个结果，请输入数字选择剧集：\n"
            "| 编号 | 类型 | 标题 |\n"
            "|------|------|------|\n"  # 添加分隔线使表格更清晰
        )
        # 遍历结果列表，最多显示前5个结果
        for index, item in enumerate(displayed_results, start=1):
            media_type = item.get("media_type", "未知")
            # 使用字典映射类型，更简洁
            type_mapping = {
                "tv": "剧集",
                "movie": "电影"
            }
            media_type_str = type_mapping.get(media_type, "未知")
            # 根据media_type选择标题字段
            if media_type == "tv":
                title = item.get("name", "未知标题")
            elif media_type == "movie":
                title = item.get("title", "未知标题")
            else:
                title = "未知标题"
            message += f"| {index} | {media_type_str} | {title} |\n"
        # 添加结果数量提示（仅在结果多时显示）
        if total_results > max_display:
            message += f"\n[仅显示前 {max_display} 个结果]\n"
        # 固定提示语
        message += "如没有目标，请输入0结束订阅并重新精确标题进行搜索。"
        return message


class subscribeTask:
    """
    订阅任务类，用于处理订阅相关操作
    """
    # 1.检查数据库中是否存在对应的项目
    @staticmethod
    async def check_tmdb_id_in_db(tmdbid: int):
        """检查数据库中是否存在对应的项目"""
        

