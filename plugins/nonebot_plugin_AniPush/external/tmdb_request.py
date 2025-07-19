
from ..config.global_config import APPCONFIG, FUNCTION
from ..constants.error_handling import AppError
from .requests import get_request
import aiohttp


class TmdbRequest:

    @staticmethod
    async def get_id_from_online(id: str, source: str) -> str | None:
        """异步获取ID"""
        if FUNCTION.tmdb_enabled is False:
            raise AppError.Exception(
                AppError.UnSupportedType, "TMDB功能未启用！请检查配置。")
            # 这里可以添加异步获取ID的逻辑
        if not id:
            raise AppError.Exception(
                AppError.ParamNotFound, "参数缺失！缺少 ID 字段")
        if not source:
            raise AppError.Exception(
                AppError.ParamNotFound, "参数缺失！缺少 source 字段")
        try:
            api = f"https://api.themoviedb.org/3/find/{id}?external_source={source}"
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {APPCONFIG.tmdb_authorization}"
            }
            proxy = APPCONFIG.proxy
            response = await get_request(api, headers=headers, proxy=proxy)
            if not response:
                raise AppError.Exception(
                    AppError.TargetNotFound, "未获取到返回数据")
            if not isinstance(response, str):
                raise AppError.Exception(
                    AppError.UnExpectedMethod, "返回数据类型错误！请检查函数方法")
            return response
        except aiohttp.ClientError as e:
            raise AppError.Exception(
                AppError.RequestError, f"网络请求失败: {str(e)}")
        except AppError.Exception as e:
            raise e
        except Exception as e:
            raise AppError.Exception(
                AppError.UnknownError, f"发生未知错误: {str(e)}")

    @staticmethod
    async def tmdb_id_verification(id: int) -> str | None:
        """异步验证ID"""
        if FUNCTION.tmdb_enabled is False:
            raise AppError.Exception(
                AppError.UnSupportedType, "TMDB功能未启用！请检查配置。")
        if not id:
            raise AppError.Exception(
                AppError.ParamNotFound, "参数缺失！缺少 ID 字段")
        if not isinstance(id, int):
            raise AppError.Exception(
                AppError.UnSupportedType, "参数类型错误！ID 应为int类型")
        try:
            api = f"https://api.themoviedb.org/3/tv/{id}"
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {APPCONFIG.tmdb_authorization}"
            }
            proxy = APPCONFIG.proxy
            response = await get_request(api, headers=headers, proxy=proxy)
            if not response:
                raise AppError.Exception(
                    AppError.TargetNotFound, "未获取到返回数据")
            if not isinstance(response, str):
                raise AppError.Exception(
                    AppError.UnExpectedMethod, "返回数据类型错误！请检查函数方法")
            return response
        except aiohttp.ClientError as e:
            raise AppError.Exception(
                AppError.RequestError, f"网络请求失败: {str(e)}")
        except AppError.Exception as e:
            raise e
        except Exception as e:
            raise AppError.Exception(
                AppError.UnknownError, f"发生未知错误: {str(e)}")
