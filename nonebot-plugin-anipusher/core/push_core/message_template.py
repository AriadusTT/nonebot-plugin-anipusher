from dataclasses import dataclass, field
from typing import Optional, List, Tuple


@dataclass
class MessageTemplate:
    """完全动态的模板处理，所有字段平等（缺失或None时跳过整行）"""
    """消息模板（使用 dataclass 定义结构）"""
    PushMessage: List[Tuple[str, Optional[str]]] = field(
        default_factory=lambda: [
            ("⬇️发现新的消息通知⬇️", None),
            ("{image}", "image"),
            ("🔴{title}", "title"),
            ("🟠集数：{episode}", "episode"),
            ("🟡集标题：{episode_title}", "episode_title"),
            ("🟢更新时间：{timestamp}", "timestamp"),
            ("🔵推送来源：{source}", "source"),
            ("🟣推送类型：{action}", "action"),
            ("🔢评分：{score}", "score"),
            ("🆔TMDB：{tmdbid}", "tmdbid"),
        ]
    )
