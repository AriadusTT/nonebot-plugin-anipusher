import aiohttp


async def get_request(url: str,
                      headers: dict | None = None,
                      params: dict | None = None,
                      proxy: str | None = None,
                      is_binary: bool = False  # 新增参数，标记是否返回二进制数据
                      ) -> bytes | str:
    """
    异步发送GET请求并返回响应内容。

    Args:
        url (str): 请求的目标URL。
        headers (dict | None): 可选的请求头字典，默认为None。
        params (dict | None): 可选的查询参数字典，默认为None。
        proxy (str | None): 可选的代理地址，默认为None。
        is_binary (bool): 标记是否返回二进制数据，默认为False（返回文本）。

    Returns:
        bytes | str: 如果is_binary为True，返回bytes类型数据；否则返回str类型数据。

    Raises:
        aiohttp.ClientResponseError: 如果HTTP响应状态码不是2XX，抛出异常。

    Notes:
        - 默认超时设置为：总超时8秒，连接超时5秒，读取超时2秒。
        - 适用于获取文本或二进制数据（如图片/文件）。
    """
    _DEFAULT_TIMEOUT = aiohttp.ClientTimeout(
        total=8,      # 总超时
        connect=5,    # 连接超时
        sock_read=2   # 读取超时
    )
    async with aiohttp.ClientSession(timeout=_DEFAULT_TIMEOUT) as session:
        async with session.get(url, headers=headers, params=params, proxy=proxy) as resp:
            resp.raise_for_status()  # 如果状态码不是 2XX，就主动抛出异常
            if is_binary:
                return await resp.read()  # 返回 bytes（用于图片/文件）
            else:
                return await resp.text()  # 返回文本（默认行为）
