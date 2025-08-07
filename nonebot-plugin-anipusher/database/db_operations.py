
from typing import Iterable
from .db_models import DatabaseTables
from .query_builder import SQLiteQueryBuilder
from ..exceptions import AppError
from .database_manager import DatabaseManager


class DatabaseService:

    # 插入或更新数据到指定表
    @staticmethod
    async def upsert_data(
        table_name: DatabaseTables.TableName,
        data: dict,
        conflict_columns: list[str] = []
    ) -> None:
        """
        插入或更新数据到指定表
        Args:
            table_name: 表名
            data: 要插入的数据字典
            conflict_columns: 冲突列名列表
        """
        # 检查参数合规性
        if not data:
            raise AppError.Exception(
                AppError.ParamNotFound, "意外的参数缺失data")
        if not isinstance(data, dict):
            raise AppError.Exception(
                AppError.UnSupportedType, f"意外的参数类型：{type(data)}")
        if not table_name:
            raise AppError.Exception(
                AppError.ParamNotFound, "意外的参数缺失table_name")
        if not isinstance(table_name, DatabaseTables.TableName):
            raise AppError.Exception(
                AppError.UnSupportedType, f"意外的参数类型：{type(table_name)}")
        # 构建插入SQL语句
        sql = SQLiteQueryBuilder.build_insert_or_update_data(
            table_name, data, conflict_columns)
        if not sql:
            raise AppError.Exception(
                AppError.UnknownError, "意外的错误：没有获取到生成的语句")
        async with DatabaseManager.get_connection() as conn:
            # 执行SQL语句
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql, data)
                    await conn.commit()
            except Exception as e:
                raise AppError.Exception(
                    AppError.DatabaseDaoError, f"数据库执行错误：{e}")

    # 查询数据
    @staticmethod
    async def select_data(
            table_name: DatabaseTables.TableName,
            columns: list[str] = [],
            where: dict = {},
            order_by: str | None = None,
            limit: int | None = None,
            offset: int | None = None) -> Iterable:
        """
        查询数据
        Args:
            table_name: 表名
            columns: 要查询的列名列表，None表示所有列
            where: WHERE条件字典 {列名: 值}
            order_by: 排序字段，如 "id DESC"
            limit: 返回记录数限制
            offset: 偏移量
        Returns:
            查询结果
        """
        if not table_name:
            raise AppError.Exception(
                AppError.ParamNotFound, "意外的参数缺失table_name")
        if not isinstance(table_name, DatabaseTables.TableName):
            raise AppError.Exception(
                AppError.UnSupportedType, f"意外的参数类型：{type(table_name)}")
        # 构建查询SQL语句

        sql = SQLiteQueryBuilder.build_select_table(
            table_name, columns, where, order_by, limit, offset)
        if not sql:
            raise AppError.Exception(
                AppError.UnknownError, "意外的错误：没有获取到生成的语句")
        async with DatabaseManager.get_connection() as conn:
            # 执行SQL语句
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql)
                    return await cursor.fetchall()
            except Exception as e:
                if "no such table" in str(e).lower():
                    raise AppError.Exception(
                        AppError.DatabaseTableNotFound, f"数据库表{table_name}不存在")
                else:
                    raise AppError.Exception(
                        AppError.DatabaseDaoError, f"数据库执行错误：{e}")

    # 更改数据
    @staticmethod
    async def update_data(
        table_name: DatabaseTables.TableName,
        update_columns: dict,
        where: dict,
        conflict_columns: list[str] = []
    ) -> None:
        """
        更新数据库表中的数据。

        Args:
            conn: 数据库连接对象。
            table_name (DatabaseTables.TableName): 目标表名，必须是 DatabaseTables.TableName 枚举类型。
            update_columns (dict): 需要更新的列及其新值，格式为 {列名: 新值}。
            where (dict): 更新条件，格式为 {列名: 条件值}。
            conflict_columns (list[str], optional): 冲突列名列表，用于处理唯一约束冲突。默认为空列表。

        Raises:
            AppError.Exception: 如果参数缺失或类型错误，抛出相应异常。
            AppError.Exception: 如果 SQL 语句生成失败或执行错误，抛出相应异常。

        Notes:
            - 该方法会检查参数的有效性，并在无效时抛出异常。
            - 使用 SQLiteQueryBuilder.build_update_table 生成 SQL 语句。
            - 执行 SQL 语句并提交事务。
        """
        if not table_name:
            raise AppError.Exception(
                AppError.ParamNotFound, "意外的参数缺失table_name")
        if not isinstance(table_name, DatabaseTables.TableName):
            raise AppError.Exception(
                AppError.UnSupportedType, "意外的参数类型table_name")
        if not update_columns:
            raise AppError.Exception(
                AppError.ParamNotFound, "意外的参数缺失updata_columns")
        if not isinstance(update_columns, dict):
            raise AppError.Exception(
                AppError.UnSupportedType, "意外的参数类型updata_columns")
        if not where:
            raise AppError.Exception(
                AppError.ParamNotFound, "意外的参数缺失where")
        if not isinstance(where, dict):
            raise AppError.Exception(
                AppError.UnSupportedType, "意外的参数类型where")
        if not isinstance(conflict_columns, list):
            raise AppError.Exception(
                AppError.UnSupportedType, "意外的参数类型conflict_columns")
        # 构建更新SQL语句
        sql = SQLiteQueryBuilder.build_update_table(
            table_name,
            update_columns,
            where,
            conflict_columns)
        if not sql:
            raise AppError.Exception(
                AppError.UnknownError, "意外的错误：没有获取到生成的语句")
        async with DatabaseManager.get_connection() as conn:
            # 执行SQL语句
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql)
                    await conn.commit()
            except Exception as e:
                raise AppError.Exception(
                    AppError.DatabaseDaoError, f"数据库执行错误：{e}")


class DatabaseSchemaManager:

    @staticmethod
    # 异步获取表元数据
    async def get_table_metadata(table_name: DatabaseTables.TableName) -> Iterable:
        """
        获取表元数据
        Args:
            table_name: 表名
        """
        if not table_name:
            raise AppError.Exception(
                AppError.ParamNotFound, "意外的表名参数缺失")
        if not isinstance(table_name, DatabaseTables.TableName):
            raise AppError.Exception(
                AppError.UnSupportedType, "意外的表名参数类型")
        try:
            sql = SQLiteQueryBuilder.build_metadata_query(table_name)
        except Exception as e:
            raise AppError.Exception(
                AppError.DatabaseDaoError, f"生成数据库语句异常：{e}")
        async with DatabaseManager.get_connection() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql)
                    return await cursor.fetchall()
            except Exception as e:
                raise AppError.Exception(
                    AppError.DatabaseDaoError, f"数据库执行错误：{e}")

    @staticmethod
    async def create_table(table_name: DatabaseTables.TableName) -> None:
        """
        创建数据库表
        Args:
            table_name: 表名
        """
        if not table_name:
            raise AppError.Exception(
                AppError.ParamNotFound, "意外的表名参数缺失")
        if not isinstance(table_name, DatabaseTables.TableName):
            raise AppError.Exception(
                AppError.UnSupportedType, "意外的表名参数类型")
        # 执行SQL语句
        try:
            columns = DatabaseTables.get_table_schema(
                table_name)
            sql = SQLiteQueryBuilder.build_create_table(table_name, columns)
        except Exception as e:
            raise AppError.Exception(
                AppError.DatabaseDaoError, f"获取数据库定义/生成数据库语句异常：{e}")
        async with DatabaseManager.get_connection() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql)
                    await conn.commit()
            except Exception as e:
                raise AppError.Exception(
                    AppError.DatabaseDaoError, f"数据库执行错误：{e}")

    @staticmethod
    async def drop_table(table_name: DatabaseTables.TableName) -> None:
        """
        删除数据库表
        Args:
            table_name: 表名
        """
        if not table_name:
            raise AppError.Exception(
                AppError.ParamNotFound, "意外的表名参数缺失")
        if not isinstance(table_name, DatabaseTables.TableName):
            raise AppError.Exception(
                AppError.UnSupportedType, "意外的表名参数类型")
        # 执行SQL语句
        try:
            sql = SQLiteQueryBuilder.build_drop_table(table_name)
        except Exception as e:
            raise AppError.Exception(
                AppError.DatabaseDaoError, f"生成数据库语句异常：{e}")
        async with DatabaseManager.get_connection() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql)
                    await conn.commit()
            except Exception as e:
                raise AppError.Exception(
                    AppError.DatabaseDaoError, f"数据库执行错误：{e}")
