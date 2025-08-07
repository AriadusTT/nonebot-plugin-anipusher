
from nonebot import get_driver
from nonebot.drivers import URL, Request, Response, ASGIMixin, HTTPServerSetup
import asyncio
from nonebot import logger
from .processing_engine import DataProcessor


class Monitor:
    def __init__(self):
        self.driver = get_driver()
        self.host = self.driver.config.host
        self.port = self.driver.config.port

    async def start_monitor(self):
        """
        启动新的监控服务
        """
        async def handle_webhook(request: Request) -> Response:
            data = request.json
            logger.opt(colors=True).info(f"<lg>获取到新的推送消息：</lg>\n{data}")
            # 在此处添加 处理流程
            asyncio.create_task(DataProcessor.create_and_run(data))
            return Response(200,
                            headers={"Content-Type": "application/json"},
                            content="ok")

        if isinstance(self.driver, ASGIMixin):
            self.driver.setup_http_server(
                HTTPServerSetup(
                    path=URL("/webhook"),
                    method="POST",
                    name="monitor_webhook",
                    handle_func=handle_webhook,
                )
            )
            logger.opt(colors=True).success(
                f"🔍 监控服务已启动，监听地址: <cyan>{self.host}:{self.port}/webhook</cyan>")
