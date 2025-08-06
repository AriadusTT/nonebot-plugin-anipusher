import aiosqlite
import asyncio
from contextlib import asynccontextmanager
from ..config import WORKDIR
from ..exceptions import AppError
from typing import Optional


class DatabaseManager:
    _instance = None
    _init_lock = asyncio.Lock()
    _max_connections = 20
    _pool: Optional[asyncio.Queue[aiosqlite.Connection]] = None
    _current_connections = 0

    def __new__(cls):
        """单例模式，确保只有一个实例"""
        # 如果实例不存在，则创建一个实例
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        # 返回实例
        return cls._instance

    @classmethod
    async def initialize(cls) -> None:
        """初始化连接池"""
        if cls._pool is None:
            async with cls._init_lock:
                if cls._pool is None:
                    cls._pool = asyncio.Queue(maxsize=cls._max_connections)
                    for _ in range(cls._max_connections):
                        conn = await cls._create_connection()
                        await cls._pool.put(conn)  # 将连接放入连接池

    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        """获取数据库连接的上下文管理器"""
        if cls._pool is None:  # 如果连接池为空，则初始化连接池
            await cls.initialize()

        try:
            if cls._pool is None:
                raise AppError.Exception(
                    AppError.DatabaseInitError, "数据库连接池未初始化")
            # 从连接池中获取连接，等待时间为5秒
            conn = await asyncio.wait_for(cls._pool.get(), timeout=5)
            cls._current_connections += 1
            try:
                yield conn
            finally:
                try:
                    await cls._pool.put(conn)
                except Exception:
                    await conn.close()
                finally:
                    cls._current_connections -= 1
        except asyncio.TimeoutError:
            raise AppError.Exception(
                AppError.DatabaseBusyError, "获取数据库连接超时")  # 如果获取连接超时，则抛出异常

    @classmethod
    async def close_pool(cls):
        """关闭所有连接"""
        if cls._pool is not None:  # 如果连接池不为空，则关闭所有连接
            async with cls._init_lock:  # 使用异步上下文管理器，保证在出现异常时，连接仍然能够关闭
                while not cls._pool.empty():  # 从连接池中取出所有连接，并关闭
                    conn = await cls._pool.get()
                    await conn.close()
                cls._pool = None
                cls._current_connections = 0

    @staticmethod
    async def _create_connection() -> aiosqlite.Connection:
        """创建新的数据库连接"""
        try:
            if not WORKDIR.data_file:
                raise AppError.Exception(
                    AppError.DatabaseInitError, "数据库文件路径异常！")

            conn = await aiosqlite.connect(
                database=WORKDIR.data_file,
                isolation_level=None,
                check_same_thread=False  # 允许在不同线程之间共享数据库连接
            )

            await conn.execute("PRAGMA journal_mode=WAL")  # 设置WAL模式
            await conn.execute("PRAGMA busy_timeout = 5000")  # 设置超时时间
            return conn

        except aiosqlite.Error as e:
            raise AppError.Exception(AppError.DatabaseError, f"数据库连接创建失败: {e}")
        except Exception as e:
            raise AppError.Exception(
                AppError.DatabaseUnknownError,
                f"未知的数据库错误: {e}"
            )
