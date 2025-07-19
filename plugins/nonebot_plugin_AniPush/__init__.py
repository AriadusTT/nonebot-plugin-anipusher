
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="nonebot-plugin-anipusher",
    description="nonebot-plugin-anipusher：一个动画更新推送插件，支持Emby及AniRss的Webhook信息推送",
    usage="nonebot-plugin-anipusher：一个动画更新推送插件，支持Emby及AniRss的Webhook信息推送",
    type="application",
    homepage="https://github.com/AriadusTT/nonebot-plugin-anipusher",
    supported_adapters={"~onebot.v11"}
)

from . import starter
