
from nonebot import get_driver


driver = get_driver()


@driver.on_startup
async def init_webhook():
    from .core.monitor_core.health_check import NewHealthCheck
    await NewHealthCheck.create_and_run()
    from .core.monitor_core.monitor import Monitor
    MONITOR = Monitor()
    await MONITOR.start_monitor()
    from .core import commands_core
