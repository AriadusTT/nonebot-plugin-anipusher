from .db_models import DatabaseTables
from nonebot import logger
from ..exceptions import AppError
from .db_operations import DatabaseSchemaManager, DatabaseService


class DBHealthCheck:

    @classmethod
    async def create_and_check(cls) -> 'DBHealthCheck':
        instance = cls()
        await instance.run_validator()
        return instance

    async def run_validator(self):
        try:
            table_names = DatabaseTables.get_table_names()
            for table_name in table_names:
                try:
                    if not isinstance(table_name, DatabaseTables.TableName):
                        raise AppError.Exception(
                            AppError.UnSupportedType, '意外的错误！表名类型错误')
                    # 查询表元数据
                    result = await DatabaseSchemaManager.get_table_metadata(table_name)
                    # 获取实际表结构
                    actual_columns = {col[1]: col for col in result}
                except AppError.Exception as e:
                    if e.error_code == AppError.DatabaseTableNotFound:
                        logger.opt(colors=True).info(
                            f'表 <b>{table_name}</b> 不存在，正在创建表')
                        await DatabaseSchemaManager.create_table(table_name)
                        logger.opt(colors=True).info(f"{table_name}表创建完成！")
                        continue  # 不再检查表结构
                    else:
                        raise
                except Exception as e:
                    raise AppError.Exception(
                        AppError.DatabaseError, f'查询表 <b>{table_name}</b> 元数据失败，错误信息：{e}')
                try:
                    except_columns = DatabaseTables.get_table_schema(
                        table_name)
                    if set(except_columns) == set(actual_columns):
                        continue
                    logger.opt(colors=True).info(
                        f'表 <b>{table_name}</b> 的元数据与预期不符，正在重建表')
                except Exception as e:
                    raise AppError.Exception(
                        AppError.UnknownError, f'对比表 <b>{table_name}</b> 元数据失败，错误信息：{e}')
                try:
                    await DatabaseSchemaManager.drop_table(table_name)
                    await DatabaseSchemaManager.create_table(table_name)
                    logger.opt(colors=True).info(f"{table_name}表重建完成！")
                except Exception as e:
                    raise AppError.Exception(
                        AppError.DatabaseError, f'重建表 <b>{table_name}</b> 失败，错误信息：{e}')
        except AppError.Exception:
            raise
        except Exception as e:
            raise AppError.Exception(
                AppError.UnknownError, f'数据库健康检查失败，错误信息：{e}')
