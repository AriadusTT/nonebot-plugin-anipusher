from .database_manager import DatabaseManager
from .table_structure import DatabaseTables
from .query_builder import SQLiteQueryBuilder
from nonebot import logger
from ..constants.error_handling import AppError


class DBHealthCheck:
    def __init__(self):
        self._conn = None

    @classmethod
    async def create_and_check(cls) -> 'DBHealthCheck':
        instance = cls()
        await instance.run_validator()
        return instance

    async def run_validator(self):
        with DatabaseManager.get_connection() as self._conn:
            # 验证表是否存在以及表结构是否正确
            self._verify_table_structure()

    def _verify_table_structure(self):
        # 第一步从数据库中获取理论上应该存在的表结构，保存在result_dict中
        try:
            table_names = DatabaseTables.get_table_names()
            if not self._conn:
                raise AppError.Exception(
                    AppError.UnSupportedType, '意外的没有数据库连接')
            result_dict = {}
            for table_name in table_names:
                if not isinstance(table_name, DatabaseTables.TableName):
                    raise AppError.Exception(
                        AppError.UnSupportedType, '意外的验证表名类型')
                sql = SQLiteQueryBuilder.build_metadata_query(table_name)
                with self._conn.cursor() as cursor:
                    cursor.execute(sql)
                    result = cursor.fetchall()  # 获取查询结果
                result_dict[table_name] = result
        except (AppError.Exception, Exception) as e:
            logger.opt(colors=True).error(f'从数据库读取表名列表失败: {e}')
            raise
        # 第二步检查结果是否符合表定义
        try:
            if not result_dict:
                raise AppError.Exception(
                    AppError.ParamNotFound, '意外的空数据result_dict')
            check_result = {}
            for table_name in result_dict:
                actual_columns = {
                    col[1]: col  # 字典的键值对
                    for col in result_dict[table_name]}
                expected_columns = DatabaseTables.get_table_schema(table_name)
                check_result[table_name] = False if set(
                    expected_columns) != set(actual_columns) else True
        except (AppError.Exception, Exception) as e:
            logger.opt(colors=True).error(f'验证表名列表失败: {e}')
            raise
        # 第三步根据结果判断是否重建表
        try:
            if not check_result:
                raise AppError.Exception(
                    AppError.ParamNotFound, '意外的空数据check_result')
            for table_name in check_result:
                if check_result[table_name] is True:
                    continue
                logger.opt(colors=True).info(f"{table_name}表结构不正确，将重建！")
                if not isinstance(table_name, DatabaseTables.TableName):
                    raise AppError.Exception(
                        AppError.UnSupportedType, '意外的数据类型')
                drop_table_sql = SQLiteQueryBuilder.build_drop_table(
                    table_name)
                create_table_sql = SQLiteQueryBuilder.build_create_table(
                    table_name, DatabaseTables.get_table_schema(table_name))
                with self._conn.cursor() as cursor:
                    cursor.execute(drop_table_sql)
                    cursor.execute(create_table_sql)
                    logger.opt(colors=True).info(f"{table_name}表重建完成！")
        except (AppError.Exception, Exception) as e:
            logger.opt(colors=True).error(f'重建表失败: {e}')
            raise
