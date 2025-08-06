import aiohttp


async def get_request(url: str,
                      headers: dict | None = None,
                      params: dict | None = None,
                      proxy: str | None = None,
                      is_binary: bool = False,
                      timeout: aiohttp.ClientTimeout | None = None
                      ) -> bytes | str:
    """
    异步发送GET请求并返回响应内容

    Args:
        url: 请求URL
        headers: 请求头
        params: 查询参数
        proxy: 代理地址
        is_binary: 是否返回二进制数据
        timeout: 自定义超时设置
    Returns:
        bytes: 当is_binary为True时返回二进制数据
        str: 当is_binary为False时返回文本数据
    Raises:
        aiohttp.ClientError: 网络请求错误
    """
    _DEFAULT_TIMEOUT = aiohttp.ClientTimeout(
        total=8,      # 总超时
        connect=5,    # 连接超时
        sock_read=2   # 读取超时
    )
    async with aiohttp.ClientSession(timeout=timeout or _DEFAULT_TIMEOUT) as session:
        async with session.get(url, headers=headers, params=params, proxy=proxy) as resp:
            resp.raise_for_status()  # 如果状态码不是 2XX，就主动抛出异常
            if is_binary:
                return await resp.read()  # 返回 bytes（用于图片/文件）
            else:
                return await resp.text()  # 返回文本（默认行为）
