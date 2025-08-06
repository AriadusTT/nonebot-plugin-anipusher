from .db_models import DatabaseTables
from ..exceptions import AppError


class SQLiteQueryBuilder:
    @staticmethod  # 创建创建表的SQL语句
    def build_create_table(table_name: DatabaseTables.TableName,
                           columns: dict[str, DatabaseTables.ColumnDef]) -> str:
        """
        根据表名和列定义生成创建表的SQL语句
        Args:
            table_name: 表名
            columns: 列定义字典，键为列名，值为列属性
        Returns:
            生成的CREATE TABLE SQL语句
        """
        column_definitions = []
        for column_name, column_def in columns.items():
            parts = [f"{column_name} {column_def['type']}"]  # 列名和类型
            # 处理NOT NULL约束
            if column_def.get('required', False):
                parts.append("NOT NULL")
            # 处理DEFAULT约束
            if 'default' in column_def and column_def['default'] is not None:
                default_value = column_def['default']
                # 根据类型处理默认值的格式
                if column_def['type'] == 'TEXT':
                    default_value = f"'{default_value}'"
                parts.append(f"DEFAULT {default_value}")

            # 处理PRIMARY KEY约束
            if column_def.get('primary_key', False):
                parts.append("PRIMARY KEY")

            # 处理AUTO_INCREMENT约束
            if column_def.get('auto_increment', False) and column_def['type'] == 'INTEGER':
                parts.append("AUTOINCREMENT")

            # 处理ALLOWED_VALUES约束
            if 'allowed_values' in column_def and column_def['allowed_values']:
                allowed_values = ", ".join(f"'{v}'" if isinstance(v, str) else str(v)
                                           for v in column_def['allowed_values'])
                parts.append(f"CHECK ({column_name} IN ({allowed_values}))")

            # 将列定义添加到列表中
            column_definitions.append(" ".join(parts))  # 拼接列定义

        # 拼接CREATE TABLE语句
        sql = f"CREATE TABLE IF NOT EXISTS {str(table_name.value)} ({', '.join(column_definitions)})"
        return sql  # 返回生成的SQL语句

    @staticmethod  # 元数据查询
    def build_metadata_query(table_name: DatabaseTables.TableName) -> str:
        sql = f"PRAGMA table_info({str(table_name.value)})"
        return sql

    @staticmethod  # 删除表
    def build_drop_table(table_name: DatabaseTables.TableName) -> str:
        sql = f"DROP TABLE IF EXISTS {str(table_name.value)}"
        return sql

    @staticmethod  # 智能覆盖插入
    def build_insert_or_update_data(table_name: DatabaseTables.TableName,
                                    data: dict,
                                    conflict_columns: list[str] = [],
                                    ) -> str | None:
        """
        生成支持智能覆盖的INSERT语句
        Args:
            table_name: 表名
            data: 要插入的数据字典（包含所有字段）
            conflict_columns: 用于检测冲突的列（必须显式指定，无默认值）

        Returns:
            带ON CONFLICT DO UPDATE的INSERT语句
        """
        try:
            # 提取所有有效字段（过滤掉None值）
            valid_data = {key: value for key,
                          value in data.items() if value is not None}
            columns = list(valid_data.keys())

            # 基础INSERT部分
            sql = f"""
            INSERT INTO {str(table_name.value)} ({', '.join(columns)})
            VALUES ({', '.join(f':{col}' for col in columns)})
            """
            # 仅当显式指定 conflict_columns 时添加 ON CONFLICT 部分
            if conflict_columns:
                # conflict_columns合法性检测
                if not isinstance(conflict_columns, list):
                    return None
                # 过滤掉 data 中不存在的列
                valid_conflict_columns = [
                    col for col in conflict_columns if col in data]
                if valid_conflict_columns:
                    # 构造ON CONFLICT DO UPDATE部分
                    update_cols = [f"{col}=excluded.{col}" for col in columns]
                    sql += f"""
                    ON CONFLICT ({', '.join(valid_conflict_columns)}) DO UPDATE SET {', '.join(update_cols)}
                    """
        except Exception as e:
            raise AppError.Exception(
                AppError.UnknownError, f"意外的错误：生成语句时出现异常{e}")
        return sql.strip()

    @staticmethod  # 查询数据的SQL语句生成器
    def build_select_table(table_name: DatabaseTables.TableName,
                           columns: list[str] | None = None,
                           where: dict | None = None,
                           order_by: str | None = None,
                           limit: int | None = None,
                           offset: int | None = None
                           ) -> str:
        """
        生成SELECT SQL查询语句

        参数:
            table_name: 表名
            columns: 要查询的列名列表，None表示所有列
            where: WHERE条件字典 {列名: 值}
            order_by: 排序字段，如 "id DESC"
            limit: 返回记录数限制
            offset: 偏移量

        返回:
            构造的SQL查询字符串
        """
        # 处理列选择
        try:
            if columns is None or len(columns) == 0:
                column_clause = "*"
            else:
                column_clause = ", ".join(columns)
            sql = f"SELECT {column_clause} FROM {str(table_name.value)}"
            # 处理WHERE条件
            if where and len(where) > 0:
                conditions = []
                for col, val in where.items():
                    if isinstance(val, str):
                        conditions.append(f"{col} = '{val}'")
                    else:
                        conditions.append(f"{col} = {val}")
                sql += " WHERE " + " AND ".join(conditions)
            # 处理排序
            if order_by:
                sql += f" ORDER BY {order_by}"
            # 处理分页
            if limit is not None:
                sql += f" LIMIT {limit}"
                if offset is not None:
                    sql += f" OFFSET {offset}"
        except Exception as e:
            raise AppError.Exception(
                AppError.UnknownError, f"意外的错误：生成语句时出现异常{e}")
        return sql.strip()

    @staticmethod  # 局部更新的SQL语句生成器
    def build_update_table(table_name: DatabaseTables.TableName,
                           update_columns: dict,
                           where: dict,
                           conflict_columns: list[str] = [],
                           ) -> str:
        """
        生成用于局部更新的SQL语句。
        Args:
            table_name (DatabaseTables.TableName): 表名，必须是DatabaseTables.TableName枚举类型。
            update_columns (dict): 需要更新的列及其新值的字典。
            where (dict): 更新条件的字典，用于指定更新的行。
            conflict_columns (list[str], optional): 冲突处理列名列表，用于SQLite的ON CONFLICT语法。默认为空列表。

        Returns:
            str: 生成的SQL更新语句。

        Raises:
            AppError.Exception: 如果参数缺失或类型错误，抛出异常。
            Exception: 其他异常。

        Notes:
            - 生成的SQL语句支持SQLite的ON CONFLICT语法。
            - 列名必须是合法的标识符，否则会抛出异常。
        """
        try:
            # SET 部分
            set_items = []
            for col, val in update_columns.items():
                if not isinstance(col, str) or not col.isidentifier():
                    raise AppError.Exception(
                        AppError.DatabaseError, f"非法列名：{col}")
                formatted_val = f"'{val}'" if isinstance(val, str) else str(val)
                set_items.append(f"{col}={formatted_val}")
            set_clause = ", ".join(set_items)
            # WHERE 部分
            where_items = []
            for col, val in where.items():
                if not isinstance(col, str) or not col.isidentifier():
                    raise AppError.Exception(
                        AppError.DatabaseError, f"非法WHERE列名：{col}")
                formatted_val = f"'{val}'" if isinstance(val, str) else str(val)
                where_items.append(f"{col}={formatted_val}")
            where_clause = " AND ".join(where_items)
            # 冲突处理（SQLite语法）
            conflict_clause = ""
            if conflict_columns:
                valid_conflict_cols = [
                    col for col in conflict_columns
                    if isinstance(col, str) and col.isidentifier()
                ]
                if valid_conflict_cols:
                    conflict_clause = f"""
                    ON CONFLICT ({', '.join(valid_conflict_cols)})
                    DO UPDATE SET {set_clause}
                    """
            # 最终SQL组装
            return f"""
            UPDATE {table_name.value}
            SET {set_clause}
            WHERE {where_clause}
            {conflict_clause}
            """.strip()
        except (AppError.Exception, Exception) as e:
            raise e
