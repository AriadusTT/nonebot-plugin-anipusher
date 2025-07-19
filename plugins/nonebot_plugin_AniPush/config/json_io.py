from pathlib import Path
from ..constants.error_handling import AppError
import json


class JsonIO:
    @staticmethod
    def read_json(path: Path) -> dict:
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
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(str(content))
        except Exception as e:
            raise AppError.Exception(AppError.ConfigIOError, f"写入配置文件失败: {e}")

    @staticmethod
    def update_json(path: Path, content: dict) -> None:
        try:
            def update(old: dict, new: dict) -> dict:

                for key, value in new.items():
                    if key in old:
                        # 如果两个值都是字典，则递归更新
                        if type(value) is not type(old[key]):
                            raise AppError.Exception(
                                AppError.UnSupportedType, f"键: {key}值类型不匹配，原始类型: {type(old[key])}, 新增类型: {type(value)}，无法更新")
                        if isinstance(value, dict):
                            update(old[key], value)
                        else:
                            # 如果两个值不是字典，则直接覆盖
                            old[key] = value
                    else:
                        # 新增键的情况
                        old[key] = value
                return old
            with open(path, "r", encoding="utf-8") as f:
                old_content = json.loads(f.read())
            new_content = update(old_content, content)
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps(new_content, indent=4, ensure_ascii=False))
        except Exception as e:
            raise AppError.Exception(AppError.ConfigIOError, f"更新配置文件失败: {e}")
