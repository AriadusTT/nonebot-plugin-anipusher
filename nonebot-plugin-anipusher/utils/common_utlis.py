from datetime import datetime, timedelta
from ..exceptions import AppError
import base64
from urllib.parse import urlparse
from pathlib import Path


class CommonUtils:
    @staticmethod  # 获取时间戳
    def get_timestamp() -> str:
        try:
            return datetime.now().isoformat(timespec='milliseconds')
        except Exception as e:
            raise AppError.Exception(AppError.UnknownError, f"获取时间戳异常：{e}")

    @staticmethod
    def img_to_base64(img_path: str | Path) -> str:
        file_path = Path(img_path) if isinstance(
            img_path, str) else img_path
        if not file_path.exists():
            raise AppError.Exception(AppError.TargetNotFound, "图片路径不存在")
        with open(file_path, "rb") as f:
            base64_data = base64.b64encode(f.read()).decode("utf-8")
        return f"base64://{base64_data}"

    @staticmethod
    def is_url(item: str) -> bool:
        try:
            result = urlparse(item)
            return all([result.scheme, result.netloc])  # 必须包含协议和网络地址
        except ValueError:
            return False

    @staticmethod
    def is_cache_img_expired(img_path: str | Path, expire_hours: float = 14 * 24) -> bool:  # 判断文件是否过期
        path = Path(img_path)
        if not Path(path).exists():
            return True
        modified_time = datetime.fromtimestamp(path.stat().st_mtime)
        return datetime.now() - modified_time > timedelta(hours=expire_hours)
