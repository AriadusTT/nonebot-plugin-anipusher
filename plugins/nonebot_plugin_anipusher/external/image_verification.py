
from ..config import APPCONFIG
from pathlib import Path
import time
from nonebot import logger
from ..constants.error_handling import AppError
from ..database import DatabaseTables
from .requests import get_request


class ImageVerification:
    """图片验证类，用于验证图片是否已存在于本地以及是否需要更新。

    该类负责处理图片的下载、更新逻辑，并根据本地图片的存在状态和更新时间决定是否下载新图片。
    如果下载失败，会返回占位图片路径；否则返回本地图片路径。

    Attributes:
        source (DatabaseTables.TableName): 数据来源标识。
        url (str): 图片的远程URL地址。
        local_path (Path): 图片的本地存储路径。
        temp_path (Path): 临时图片存储路径。
        placeholder_path (Path): 占位图片路径。
    """

    def __init__(self, source: DatabaseTables.TableName, url: str, local_path: Path):
        """初始化图片验证类。

        Args:
            source (DatabaseTables.TableName): 数据来源标识。
            url (str): 图片的远程URL地址。
            local_path (Path): 图片的本地存储路径。
        """
        self.source = source
        self.url = url
        self.local_path = local_path
        self.temp_path = Path(__file__).resolve(
        ).parents[1] / "covers" / local_path.name    # 临时图片路径
        self.placeholder_path = Path(__file__).resolve(
        ).parents[1] / "others" / "placeholder_image.jpg"  # 占位图片

    async def process(self) -> Path:
        """异步处理图片下载或更新逻辑。

        根据本地图片是否存在以及是否需要更新（超过14天未更新），决定是否下载图片。
        如果下载失败，返回占位图片路径；否则返回本地图片路径。

        Returns:
            Path: 图片的本地路径或占位图片路径。
        """
        # 数据验证
        self._data_verification()
        download_identifier = False
        if not self.local_path.exists():  # 本地不存在该图片,则下载,并保存至本地
            download_identifier = True
        else:  # 本地存在该图片,则判断是否需要更新
            last_modified = self.local_path.stat().st_mtime
            if time.time() - last_modified > 14 * 24 * 3600:  # 十四天更新一次
                download_identifier = True
        if download_identifier:
            self.local_path.parent.mkdir(parents=True, exist_ok=True)
            binary = await self._download_binary()
            try:
                with open(self.temp_path, "wb") as f:
                    f.write(binary)
                self.temp_path.replace(self.local_path)
            except Exception as e:
                self.temp_path.unlink(missing_ok=True)
                logger.opt(colors=True).warning(
                    f"<y>{self.source.value}</y>：封面图片下载异常：{e}")
                return self.placeholder_path
            logger.opt(colors=True).info(
                f"<g>{self.source.value}</g>：封面图片下载成功")
            return self.local_path
        else:
            return self.local_path

    def _data_verification(self):  # 数据验证
        if not self.local_path or not isinstance(self.local_path, Path):
            raise AppError.Exception(
                AppError.UnknownError, f"本地路径异常或类型异常：{self.local_path}，类型：{type(self.local_path)}")
        if not self.url or not isinstance(self.url, str):
            raise AppError.Exception(
                AppError.UnknownError, f"图片链接异常或类型异常：{self.url}，类型：{type(self.url)}")
        if not self.source or not isinstance(self.source, DatabaseTables.TableName):
            raise AppError.Exception(
                AppError.UnknownError, f"来源异常或类型异常：{self.source}，类型：{type(self.source)}")

    async def _download_binary(self):
        """
        异步下载二进制数据（如图片）的方法。

        根据数据来源（ANI_RSS 或 EMBY）设置请求头，并下载二进制数据。
        如果下载的数据类型不是 bytes，会抛出异常。

        返回:
            bytes: 下载的二进制数据。

        异常:
            AppError.Exception: 如果下载过程中出现错误或数据类型不匹配。
        """
        if self.source == DatabaseTables.TableName.ANI_RSS:
            headers = {
                "User-Agent": "AriadusTTT/nonebot_plugin_AniPush/1.0.0 (Python)"
            }
        elif self.source == DatabaseTables.TableName.EMBY:
            headers = {
                "X-Emby-Token": APPCONFIG.emby_key,
                "User-Agent": "AriadusTTT/nonebot_plugin_AniPush/1.0.0 (Python)"
            }
        try:
            binary = await get_request(url=self.url, headers=headers, is_binary=True)
            if not isinstance(binary, bytes):
                raise AppError.Exception(
                    AppError.UnSupportedType, "封面图片下载异常，返回数据类型错误")
        except AppError.Exception as e:
            raise e
        except Exception as e:
            raise AppError.Exception(
                AppError.UnknownError, f"图片下载异常：{e}")
        return binary
