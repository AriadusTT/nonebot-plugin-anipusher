
import sqlite3
import threading
from pathlib import Path
from dbutils.pooled_db import PooledDB

from ..constants.error_handling import AppError

"""
    数据库连接池管理类

    该类提供了线程安全的SQLite数据库连接池管理功能，包括：
    - 获取数据库连接 (get_connection)
    - 关闭连接池 (close_pool)

    使用单例模式和线程锁确保线程安全，最大连接数默认为10。
    异常处理使用自定义的AppError异常体系。

    注意：_create_pool, _init_pool是内部实现方法，不建议直接调用。
"""


class DatabaseManager:
    _pool = None
    _init_lock = threading.Lock()  # 新增初始化锁

    @classmethod  # 获取数据库连接
    def get_connection(cls):
        """获取数据库连接（线程安全）"""
        if cls._pool is None:
            cls._init_pool()
        if cls._pool is None:
            raise AppError.Exception(AppError.DatabaseInitError, "数据库连接池初始化异常")
        return cls._pool.connection()

    @classmethod  # 关闭连接池
    def close_pool(cls):
        """关闭连接池并释放资源"""
        with cls._init_lock:
            if cls._pool:
                cls._pool.close()
                cls._pool = None

    @classmethod  # 初始化连接池
    def _init_pool(cls):
        with cls._init_lock:  # 使用锁来确保线程安全
            if cls._pool is None:
                cls._pool = cls._create_pool()

    @staticmethod  # 创建连接池
    def _create_pool():
        db_path = Path(__file__).resolve(
        ).parent / "database.db"
        try:
            # 创建连接池
            pool = PooledDB(
                creator=sqlite3,
                maxconnections=10,
                database=db_path,
                blocking=True,
                check_same_thread=False  # 允许跨线程操作
            )  # 创建连接池sqlite3，大小为10
            return pool
        except sqlite3.Error as e:
            raise AppError.Exception(AppError.DatabaseError, f"数据库连接池创建失败{e}")
        except Exception as e:
            raise AppError.Exception(
                AppError.DatabaseUnknownError, f"未知的数据库错误:{e}")
