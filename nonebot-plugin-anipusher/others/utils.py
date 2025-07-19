import base64

from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime
from ..constants.error_handling import AppError
from ..database import DatabaseTables


class PublicUtils:
    @staticmethod  # 获取时间戳
    def get_timestamp() -> str:
        try:
            return datetime.now().isoformat(timespec='milliseconds')
        except Exception as e:
            raise AppError.Exception(AppError.UnknownError, f"获取时间戳异常：{e}")

    @staticmethod  # 将本地图片转换成base64编码
    def get_base64_img_url(file_path: str | Path) -> str:
        if not file_path:
            raise AppError.Exception(AppError.ParamNotFound, "文件路径为空！")
        # 统一转成 Path 对象，方便检查
        file_path = Path(file_path) if isinstance(
            file_path, str) else file_path
        if not file_path.exists():
            raise AppError.Exception(
                AppError.ParamNotFound, f"{file_path}文件不存在！")
        try:
            with open(file_path, "rb") as f:
                base64_data = base64.b64encode(
                    f.read()).decode('utf-8')  # 直接 decode
                return f"base64://{base64_data}"
        except IOError as e:
            raise AppError.Exception(
                AppError.UnknownError, f"转换图片为base64失败: {e}")

    @staticmethod  # 拼接Emby图片链接
    def get_emby_image_url(host: str | None, id: str | None, tag: str | None) -> str:
        # 检查参数是否为空
        if not host:
            raise AppError.Exception(AppError.MissingData, "host参数不能为空")
        if not id:
            raise AppError.Exception(AppError.MissingData, "id参数不能为空")
        if not tag:
            raise AppError.Exception(AppError.MissingData, "tag参数不能为空")

        # 检查参数类型
        if not isinstance(host, str):
            raise AppError.Exception(
                AppError.UnSupportedType, f"错误的host类型：{type(host)} expected str")
        if not isinstance(id, str):
            raise AppError.Exception(
                AppError.UnSupportedType, f"错误的ID类型：{type(id)} expected str")
        if not isinstance(tag, str):
            raise AppError.Exception(
                AppError.UnSupportedType, f"错误的tag类型：{type(host)} expected str")

        return f"{host.rstrip('/')}/emby/Items/{id}/Images/Primary?tag={tag}&quality=90"

    @staticmethod  # 拼接Emby系列链接
    def get_emby_series_url(host: str | None, series_id: str | None, server_id: str | None) -> str:
        # 检查参数是否为空
        if not host:
            raise AppError.Exception(AppError.MissingData, "host参数不能为空")
        if not series_id:
            raise AppError.Exception(AppError.MissingData, "id参数不能为空")
        if not server_id:
            raise AppError.Exception(AppError.MissingData, "tag参数不能为空")

        # 检查参数类型
        if not isinstance(host, str):
            raise AppError.Exception(
                AppError.UnSupportedType, "host参数类型错误，应为str")
        if not isinstance(series_id, str):
            raise AppError.Exception(
                AppError.UnSupportedType, "id参数类型错误，应为str")
        if not isinstance(server_id, str):
            raise AppError.Exception(
                AppError.UnSupportedType, "tag参数类型错误，应为str")

        return f"{host.rstrip('/')}/web/index.html#!/item?id={series_id}&serverId={server_id}"

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        检查字符串是否为合法的 URL。

        Args:
            url (str): 待检查的字符串。

        Returns:
            bool: 如果 URL 合法返回 True，否则返回 False。
        """
        try:
            result = urlparse(url)
            # 基本检查：必须有 scheme（如 http）和 netloc（如 example.com）
            if not all([result.scheme, result.netloc]):
                return False
            # 检查 scheme 是否合法（如 http/https/ftp）
            if result.scheme not in {"http", "https", "ftp"}:
                return False
            # 检查 netloc（域名）是否包含至少一个点（避免 "http://localhost" 被误判）
            if "." not in result.netloc and "localhost" not in result.netloc:
                return False
            return True
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def infer_image_local_path(source: DatabaseTables.TableName, url: str) -> Path:
        if not url:
            raise AppError.Exception(AppError.MissingData, "url参数为空！")
        if not source:
            raise AppError.Exception(AppError.MissingData, "source参数为空！")
        base_path = Path(__file__).resolve(
        ).parents[1] / "covers" / source.value
        if source == DatabaseTables.TableName.ANI_RSS:
            file_name = Path(urlparse(url).path).name
            return base_path / file_name
        elif source == DatabaseTables.TableName.EMBY:
            return base_path / f"{url}.jpg"
        else:
            raise AppError.Exception(AppError.UnknownError, "未知的source参数！")
