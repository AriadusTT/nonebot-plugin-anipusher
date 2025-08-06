

from .starter import init_webhook
from nonebot.plugin import PluginMetadata
from nonebot import require

__plugin_meta__ = PluginMetadata(
    name="动画推送机",
    description="nonebot-plugin-anipusher：一个动画更新推送插件，支持Emby及AniRss的Webhook信息推送",
    usage="nonebot-plugin-anipusher：一个动画更新推送插件，支持Emby及AniRss的Webhook信息推送",
    type="application",
    homepage="https://github.com/AriadusTT/nonebot-plugin-anipusher",
    supported_adapters={"~onebot.v11"}
)

require("nonebot_plugin_localstore")
