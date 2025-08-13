
from nonebot import get_driver


driver = get_driver()


@driver.on_startup
async def init_webhook():
    # 启动前配置及自检
    from .core.health_checker import HealthCheck
    await HealthCheck.create_and_run()
    # 启动webhook接收器
    from .core.monitor_core.monitor import Monitor
    moniter = Monitor()
    await moniter.start_monitor()
    # 启动命令匹配
    from .core import commands_core
