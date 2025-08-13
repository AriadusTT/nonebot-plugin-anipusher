
from ..config import APPCONFIG, FUNCTION
from ..exceptions import AppError
from .requests import get_request
import aiohttp
import json
from typing import Literal


class TmdbClient:
    @staticmethod
    async def _request_tmdb_api(
        endpoint: str,
        params: dict | None = None
    ) -> dict | None:
        """
        异步请求TMDB API
        Args:
            endpoint: API端点路径 (如 "find/123")
            params: 查询参数字典
        Returns:
            解析后的JSON数据字典
        Raises:
            AppError.Exception: 各种业务错误
        """
        if not FUNCTION.tmdb_enabled:
            raise AppError.Exception(
                AppError.UnExpectedMethod, "TMDB功能未启用")
        url = f"https://api.themoviedb.org/3/{endpoint.lstrip('/')}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {APPCONFIG.tmdb_authorization}"
        }
        try:
            response = await get_request(
                url,
                headers=headers,
                params=params,
                proxy=APPCONFIG.proxy
            )
            if not response:
                raise AppError.Exception(
                    AppError.ResponseNotFound, "未获取到返回数据")
            if not isinstance(response, str):
                raise AppError.Exception(
                    AppError.UnSupportedType, "返回数据类型错误！")
        except aiohttp.ClientError as e:
            raise AppError.Exception(
                AppError.RequestError, f"网络请求失败: {str(e)}")
        except AppError.Exception as e:
            raise e
        except Exception as e:
            raise AppError.Exception(
                AppError.UnknownError, f"发生未知错误: {str(e)}")
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise AppError.Exception(
                AppError.UnknownError, f"返回数据解析失败: {str(e)}")
        except Exception as e:
            raise AppError.Exception(
                AppError.UnknownError, f"发生未知错误: {type(e).__name__}: {str(e)}")

    @staticmethod
    async def find_by_external_id(id: str, source: str) -> dict | None:
        """异步通过外部ID查找"""
        # 判断ID是否为空
        if not id:
            # 抛出异常，提示参数缺失，缺少ID字段
            raise AppError.Exception(
                AppError.MissingData, "参数缺失！缺少 ID 字段")
        if not source:
            raise AppError.Exception(
                AppError.MissingData, "参数缺失！缺少 source 字段")
        endpoint = f"find/{id}?external_source={source}"
        return await TmdbClient._request_tmdb_api(endpoint)

    @staticmethod
    async def get_id_details(id: int, type: Literal["Movie", "Episode", "Series"] = "Episode") -> dict | None:
        """异步获取ID的详细信息"""
        if not id:
            raise AppError.Exception(
                AppError.MissingData, "参数缺失！缺少 ID 字段")
        if not isinstance(id, int):
            raise AppError.Exception(
                AppError.UnSupportedType, "参数类型错误！ID 应为int类型")

        endpoint = f"{type}/{id}"
        return await TmdbClient._request_tmdb_api(endpoint)

    @staticmethod
    async def search_by_multi(query: str) -> dict | None:
        """异步通过多条件搜索"""
        if not query:
            raise AppError.Exception(
                AppError.MissingData, "参数缺失！缺少标题字段")
        if not isinstance(query, str):
            raise AppError.Exception(
                AppError.UnSupportedType, "参数类型错误！query应为str类型")
        endpoint = f"search/multi?query={query}&include_adult=true&language=zh-CN&page=1"
        return await TmdbClient._request_tmdb_api(endpoint)
