from ..exceptions import AppError
from ..config import WORKDIR
import json
import shutil


class JsonStorage:
    """Json文件存储类"""
    @staticmethod
    async def read():
        try:
            if not WORKDIR.config_file:
                raise AppError.Exception(AppError.ParamNotFound, "配置文件路径缺失")
            if not WORKDIR.config_file.exists():
                raise AppError.Exception(
                    AppError.MissingData, f"配置文件不存在: {WORKDIR.config_file}")
            return json.loads(WORKDIR.config_file.read_text(encoding="utf-8"))
        except Exception:
            raise

    @staticmethod
    async def write(data):
        try:
            if not WORKDIR.config_file:
                raise AppError.Exception(AppError.ParamNotFound, "配置文件路径缺失")
            if not WORKDIR.config_file.exists():
                raise AppError.Exception(
                    AppError.MissingData, f"配置文件不存在: {WORKDIR.config_file}")
            WORKDIR.config_file.write_text(
                json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
        except Exception:
            raise

    @staticmethod
    async def update(content: dict) -> None:
        """递归更新配置文件内容（原子操作，线程安全）"""
        def deep_update(old: dict, new: dict) -> dict:
            """递归合并字典，保留原有键值"""
            for key, value in new.items():
                if key in old:
                    if not isinstance(value, type(old[key])):
                        raise AppError.Exception(
                            AppError.UnSupportedType,
                            f"键 '{key}' 类型冲突（原类型: {type(old[key])}, 新类型: {type(value)}）"
                        )
                    if isinstance(value, dict):
                        deep_update(old[key], value)
                    else:
                        old[key] = value
                else:
                    old[key] = value
            return old
        try:
            # 1. 检查配置文件路径
            if not WORKDIR.config_file:
                raise AppError.Exception(AppError.MissingData, "未指定配置文件路径")
            if not WORKDIR.config_file.exists():
                raise AppError.Exception(
                    AppError.MissingData, f"配置文件不存在: {WORKDIR.config_file}")
            # 准备临时文件路径
            temp_path = WORKDIR.config_file.with_suffix(".tmp")
            # 读取原内容（文件不存在时初始化空字典）
            try:
                old_content = json.loads(
                    WORKDIR.config_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                raise AppError.Exception(AppError.ConfigIOError, "配置文件格式错误")
            except FileNotFoundError:
                old_content = {}
            # 3. 类型检查与合并
            if not isinstance(old_content, dict):
                raise AppError.Exception(AppError.UnSupportedType, "配置文件必须为字典格式")
            # 4. 写入临时文件
            temp_path.write_text(
                json.dumps(deep_update(old_content, content), indent=4, ensure_ascii=False), encoding="utf-8")
            # 5. 替换原文件
            shutil.move(temp_path, WORKDIR.config_file)
        except Exception as e:
            # 清理临时文件
            if "temp_path" in locals() and temp_path.exists():
                temp_path.unlink()
            raise AppError.Exception(AppError.ConfigIOError, f"更新配置文件失败: {e}")
