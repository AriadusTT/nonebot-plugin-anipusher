from datetime import datetime
from ..exceptions import AppError


class TimeUtils:
    @staticmethod  # 获取时间戳
    def get_timestamp() -> str:
        try:
            return datetime.now().isoformat(timespec='milliseconds')
        except Exception as e:
            raise AppError.Exception(AppError.UnknownError, f"获取时间戳异常：{e}")
