from typing import Any
from .database_manager import DatabaseManager
from .db_models import DatabaseTables
from nonebot import logger
from .query_builder import SQLiteQueryBuilder
from ..exceptions import AppError


class DBHealthCheck:

    @classmethod
    async def create_and_check(cls) -> 'DBHealthCheck':
        instance = cls()
        await instance.run_validator()
        return instance

    async def run_validator(self):
        try:
            table_names = DatabaseTables.get_table_names()
            async with DatabaseManager().get_connection() as _conn:
                if not _conn:
                    raise AppError.Exception(
                        AppError.DatabaseError, '未获取到数据库连接')
                    # 禁用外键约束以便重建表
                await _conn.execute("PRAGMA foreign_keys=OFF")  # 禁用外键约束以便重建表
                for table_name in table_names:
                    try:
                        if not isinstance(table_name, DatabaseTables.TableName):
                            raise AppError.Exception(
                                AppError.UnSupportedType, '意外的错误！表名类型错误')
                        sql = SQLiteQueryBuilder.build_metadata_query(
                            table_name)
                        cursor = await _conn.execute(sql)
                        # 获取查询结果
                        actual_columns = {col[1]: col for col in await cursor.fetchall()}
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
                        # 删除表
                        drop_table_sql = SQLiteQueryBuilder.build_drop_table(
                            table_name)
                        await _conn.execute(drop_table_sql)
                        # 创建表
                        create_table_sql = SQLiteQueryBuilder.build_create_table(
                            table_name, except_columns)
                        await _conn.execute(create_table_sql)
                        # 提交事务
                        await _conn.commit()
                        logger.opt(colors=True).info(f"{table_name}表重建完成！")
                    except Exception as e:
                        raise AppError.Exception(
                            AppError.DatabaseError, f'重建表 <b>{table_name}</b> 失败，错误信息：{e}')
                await _conn.execute("PRAGMA foreign_keys=ON")  # 启用外键约束
        except AppError.Exception:
            raise
        except Exception as e:
            raise AppError.Exception(
                AppError.UnknownError, f'数据库健康检查失败，错误信息：{e}')
