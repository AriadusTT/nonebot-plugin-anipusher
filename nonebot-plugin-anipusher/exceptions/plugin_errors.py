
from enum import Enum
from typing import NoReturn


"""
    错误代码枚举和异常处理类

    属性:
        code (int): 错误状态码
        msg (str): 错误状态描述

    方法:
        get_by_code(code): 根据状态码获取对应的枚举项
        raise_(extra_msg): 抛出此错误对应的异常，可附加额外信息

    异常类:
        Exception: 自定义异常类，包含错误代码和额外信息

# 使用示例
try:
    AppError.XxxError.raise_("连接超时")  # 最简洁的抛出方式
    # 或者保持原有风格（如需）:
    raise AppError.Exception(AppError.ConfigNotFound, "文件不存在")
except AppError.Exception as e:
    print(f"捕获到错误: {e}")
    print(f"错误码: {e.error_code.code}")
    print(f"错误信息: {e.error_code.msg}")
"""


class AppError(Enum):
    """错误代码枚举和异常处理类"""

    # 错误码
    # 通用错误
    UnknownError = (0, "未知错误")
    ParamNotFound = (1001, "参数不存在")
    TargetNotFound = (1002, "目标不存在")
    ConfigIOError = (1003, "配置文件读写错误")
    IoError = (1004, "IO错误")
    GlobalConfigError = (1005, "全局配置错误")
    UnSupportedType = (1006, "不支持的数据类型")
    UnKnowSource = (1007, "未知数据源")
    UnExpectedMethod = (1008, "不支持的请求方法")
    InvalidLength = (1009, "长度不符合要求")
    MissingData = (1010, "缺失数据")

    DatabaseUnknownError = (2000, "数据库未知错误")
    DatabaseError = (2001, "数据库错误")
    DatabaseInitError = (2002, "数据库初始化错误")
    DatabaseDaoError = (2003, "数据库DAO错误")
    DatabaseBusyError = (2004, "数据库繁忙")
    DatabaseRecordNotFound = (2005, "数据库记录未找到")
    DatabaseTableNotFound = (2006, "数据库表不存在")

    RequestError = (3000, "请求错误")
    RequestTimeout = (3001, "请求超时")
    RequestFailed = (3002, "请求失败")
    RequestInvalidResponse = (3003, "请求返回无效响应")
    RequestInvalidJson = (3004, "请求返回无效JSON")
    RequestInvalidUrl = (3005, "请求URL无效")
    ResponseNotFound = (3006, "响应未找到")

    @property
    def code(self):
        """获取状态码"""
        return self.value[0]

    @property
    def msg(self):
        """获取状态描述"""
        return self.value[1]

    def __str__(self):
        """字符串表示"""
        return f"[{self.code}] {self.msg}"

    @classmethod
    def get_by_code(cls, code):
        """根据状态码获取枚举项"""
        for member in cls:
            if member.code == code:
                return member
        return None

    def raise_(self, extra_msg: str = "") -> NoReturn:
        """抛出此错误对应的异常"""
        raise self.Exception(self, extra_msg)

    class Exception(Exception):
        def __init__(self, error_code: 'AppError', extra_msg: str = ""):
            self.error_code = error_code
            self.extra_msg = extra_msg
            super().__init__(f"{error_code.msg} {extra_msg}".strip())

        def __str__(self):
            return f"[{self.error_code.code}] {super().__str__()}"
