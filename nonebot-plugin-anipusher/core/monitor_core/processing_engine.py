from ...exceptions import AppError
from ...database import DatabaseTables
from ..monitor_core.abstract_processor import AbstractDataProcessor
from nonebot import logger


class DataProcessor():  # 数据处理
    def __init__(self, data):
        self.data = data  # 待处理数据
        self.source = None  # 数据源

    # 初始化&主入口
    @classmethod
    async def create_and_run(cls, data) -> 'DataProcessor':
        instance = cls(data)
        await instance.main_process()
        return instance

    async def main_process(self):
        """
        主处理流程
        1. 数据源解析
        2. 选择对应的处理器
        3. 执行处理流程
        """
        try:
            self.source = self.source_analyze()  # 数据源解析
            logger.opt(colors=True).info(
                f"解析到数据源：{self.source.value}，指定处理器处理数据")
        except (AppError.Exception, Exception) as e:
            raise e
        if self.source is None:
            raise AppError.Exception(
                AppError.UnKnowSource, "数据源解析失败：无法识别数据源类型")
        try:
            processor = await AbstractDataProcessor.select_processor(
                self.data, self.source)  # 选择对应的处理器
            if not processor:
                raise AppError.Exception(
                    AppError.UnKnowSource, f"数据源解析失败：未找到对应的处理器，数据源类型：{self.source.value}")
            await processor.execute()  # 执行处理流程
        except (AppError.Exception, Exception) as e:
            raise e

    def source_analyze(self):
        """
        数据源解析类，用于分析并确定数据来源类型

        静态方法:
            analyze(data=None): 分析输入数据并返回对应的数据表类型
                参数:
                    data: 待分析的字典数据
                返回:
                    DatabaseTables.TableName: 对应的数据表枚举值
                异常:
                    AppError.Exception: 当数据类型错误、数据为空或无法识别数据源时抛出
        """
        if not isinstance(self.data, dict):
            raise AppError.Exception(
                AppError.UnSupportedType, "数据源解析失败：数据类型错误，必须为字典类型")
        if not self.data:
            raise AppError.Exception(
                AppError.ParamNotFound, "数据源解析失败：数据为空")
        analyze_key = next(iter(self.data), None)  # 避免StopIteration
        if not analyze_key:
            raise AppError.Exception(
                AppError.ParamNotFound, "数据源解析失败：数据缺少关键字段")
        analyze_key = analyze_key.lower()  # 统一小写处理

        # 基于分析出的字段，给出对应的解析器
        if analyze_key == 'title':
            return DatabaseTables.TableName.EMBY
        elif analyze_key == 'ani':
            return DatabaseTables.TableName.ANI_RSS
        raise AppError.Exception(
            AppError.UnKnowSource, "数据源解析失败：未知数据源类型")
