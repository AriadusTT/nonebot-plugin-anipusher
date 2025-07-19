
from fastapi import Request
import asyncio
from fastapi.responses import JSONResponse, PlainTextResponse
from nonebot import get_driver, get_app
from .processing_engine import DataProcessor
from nonebot import logger


class Monitor:
    def __init__(self):
        self.driver = get_driver()
        self.app = get_app()
        self.host = self.driver.config.host
        self.port = self.driver.config.port

    async def start_monitor(self):
        """
        启动监控服务
        """
        # 这里可以添加更多的监控逻辑
        @self.app.post("/webhook")
        async def monitor(request: Request):
            data = await request.json()
            logger.opt(colors=True).info(f"<lg>收到监控请求</lg>\n{data}")
            asyncio.create_task(DataProcessor.create_and_run(data))
            return JSONResponse(status_code=200, content={"message": "ok"})
        logger.opt(colors=True).success(
            f"🔍 监控服务已启动，监听地址: <cyan>{self.host}:{self.port}/webhook</cyan>")

        @self.app.get("/webhook")
        async def monitor_page(request: Request):
            """
            监控页面
            """
            return PlainTextResponse(
                "这是一个监控 Webhook 端点，请使用 POST 方法发送 JSON 数据到此端点。\n"
                f"监控服务运行中，地址: {self.host}:{self.port}/webhook"
            )
