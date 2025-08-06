from pathlib import Path
from ..exceptions import AppError
import json


class JsonIO:
    """
    提供JSON文件读写功能的工具类
    """
    @staticmethod
    def read_json(path: Path) -> dict:
        """
        读取JSON文件内容
        Args:
            path: 文件路径(Path对象)
        Returns:
            dict: 解析后的字典数据
        Raises:
            AppError.Exception: 当文件不存在或读取失败时抛出
        """
        try:
            if not path.is_file():
                raise AppError.Exception(AppError.TargetNotFound, "配置文件不存在")
            with open(path, "r", encoding="utf-8") as f:
                return json.loads(f.read())
        except AppError.Exception:
            raise
        except Exception as e:
            raise AppError.Exception(AppError.ConfigIOError, f"读取配置文件失败: {e}")

    @staticmethod
    def write_json(path: Path, content: dict) -> None:
        """
        写入JSON文件
        Args:
            path: 文件路径(Path对象)
            content: 要写入的字典数据
        Raises:
            AppError.Exception: 当写入失败时抛出
        """
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(str(content))
        except Exception as e:
            raise AppError.Exception(AppError.ConfigIOError, f"写入配置文件失败: {e}")

    @staticmethod
    def update_json(path: Path, content: dict) -> None:
        """
        更新JSON文件(保留原有键值，只更新指定的键值)

        Args:
            path: 文件路径(Path对象)
            content: 要更新的字典数据
        Raises:
            AppError.Exception: 当更新失败或类型不匹配时抛出
        """
        try:
            def update(old: dict, new: dict) -> dict:
                """
                递归更新字典
                Args:
                    old: 原始字典
                    new: 新字典
                Returns:
                    dict: 更新后的字典
                """
                for key, value in new.items():
                    if key in old:
                        if type(value) is not type(old[key]):
                            raise AppError.Exception(
                                AppError.UnSupportedType, f"键: {key}值类型不匹配，原始类型: {type(old[key])}, 新增类型: {type(value)}，无法更新")
                        if isinstance(value, dict):
                            update(old[key], value)
                        else:
                            old[key] = value
                    else:
                        old[key] = value
                return old
            with open(path, "r", encoding="utf-8") as f:
                old_content = json.loads(f.read())
            new_content = update(old_content, content)
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps(new_content, indent=4, ensure_ascii=False))
        except Exception as e:
            raise AppError.Exception(AppError.ConfigIOError, f"更新配置文件失败: {e}")
