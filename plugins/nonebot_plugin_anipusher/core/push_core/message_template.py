

class MessageTemplate:
    """完全动态的模板处理，所有字段平等（缺失或None时跳过整行）"""

    # 定义完整的模板结构（按行拆分，每行关联一个字段）
    PUSH_HEAD: list[tuple[str, None]] = [
        ("⬇️发现新的消息通知⬇️", None)
    ]

    PUSH_BODY: list[tuple[str, str | None]] = [
        ("🔴{title}", "title"),
        ("🟠集数：{episode}", "episode"),
        ("🟡集标题：{episode_title}", "episode_title"),
        ("🟢更新时间：{timestamp}", "timestamp"),
        ("🔵推送来源：{source}", "source"),
        ("🟣推送类型：{action}", "action"),
        ("🔢评分：{score}", "score"),
        ("🆔TMDB：{tmdbid}", "tmdbid")
    ]

    Subscriber = [("订阅提醒：", None)]
