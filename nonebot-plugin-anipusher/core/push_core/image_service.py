import asyncio
import shutil
from pathlib import Path
from typing import Literal
from nonebot import logger

from ...config import WORKDIR, APPCONFIG, FUNCTION
from ...utils import CommonUtils, EmbyUtils
from ...exceptions import AppError
from ...external import get_request


class ImageProcessor:
    def __init__(self, image_queue: list, emby_series_id: str | None = None, tmdb_id: str | None = None) -> None:
        self.image_queue = image_queue
        self.emby_series_id = emby_series_id
        self.tmdb_id = tmdb_id
        self.is_image_expired = False  # 图片是否过期
        self.output_img = None  # 最终图片输出路径

    async def process(self) -> Path | None:
        # 先搜索本地存储
        self.output_img = self._search_in_localstore()  # 如果有且未过期，则设置output_img并返回，否则继续
        if self.output_img:
            if self.is_image_expired:
                logger.opt(colors=True).info(
                    '<y>Pusher</y>：发现可用的本地图片，但图片已过期，尝试重新获取')
            else:
                logger.opt(colors=True).info(
                    '<g>Pusher</g>：发现可用的本地图片，使用本地图片')
                return self.output_img
        # 尝试从图片队列中获取↓
        # 如果没有图片队列，则返回默认图片
        if not self.image_queue:
            if self.output_img:
                logger.opt(colors=True).info(
                    '<y>Pusher</y>：获取新图片失败，回退使用超期图片')
                return self.output_img
            logger.opt(colors=True).info('<y>Pusher</y>：没有获取到图片，回退使用默认图片')
            return self._default_image()
        # 如果有图片队列,首先清洗图片队列，生成只有url的队列
        cleaned_urls = self._clean_image_queue()
        # 如果清洗后没有图片，则返回默认图片
        if not cleaned_urls:
            if self.output_img:
                logger.opt(colors=True).info(
                    '<y>Pusher</y>：获取新图片失败，回退使用超期图片')
                return self.output_img
            logger.opt(colors=True).info('<y>Pusher</y>：没有获取到可用图片，使用默认图片')
            return self._default_image()
        # 如果清洗后还有图片，则尝试下载图片，返回首个可用的图片的二进制
        image_data = await self._download_first_valid_image(cleaned_urls)
        if not image_data:
            if self.output_img:
                logger.opt(colors=True).info(
                    '<y>Pusher</y>：获取新图片失败，回退使用超期图片')
                return self.output_img
            logger.opt(colors=True).info('<y>Pusher</y>：没有获取到可用图片，使用默认图片')
            return self._default_image()
        # 如果成功获取到图片，则保存到本地，返回保存路径
        img_path = await self._save_bytes_to_cache(image_data)
        if img_path:
            self.output_img = img_path
            logger.opt(colors=True).info('<g>Pusher</g>：刷新图片缓存 <g>完成</g>')
            return self.output_img
        else:
            if self.output_img:
                logger.opt(colors=True).info(
                    '<y>Pusher</y>：获取新图片失败，回退使用超期图片')
                return self.output_img
            logger.opt(colors=True).info('<y>Pusher</y>：没有获取到可用图片，使用默认图片')
            return self._default_image()

    # 在本地存储中查找图片，如果找不到，则返回None，等待后续处理
    def _search_in_localstore(self) -> None | Path:
        try:
            if not self.tmdb_id:
                raise AppError.Exception(
                    AppError.MissingData, "项目TMDB ID缺失！")
            if not WORKDIR.cache_dir:
                raise AppError.Exception(AppError.MissingData, "项目缓存目录缺失！")
            local_img_path = WORKDIR.cache_dir / f"{self.tmdb_id}.jpg"
            # 如果本地存在图片，且未过期，则直接返回base64编码
            if not local_img_path.exists():
                return None
            # 如果图片未过期，则直接返回base64编码
            if CommonUtils.is_cache_img_expired(local_img_path):
                self.is_image_expired = True
            return local_img_path
        except Exception as e:
            logger.opt(colors=True).warning(
                f"<y>Pusher</y>：获取本地图片失败，错误信息：{e}")
            return None

    # 获取默认图片
    def _default_image(self) -> Path | None:
        try:
            if not WORKDIR.cache_dir:
                raise AppError.Exception(AppError.MissingData, "项目缓存目录缺失！")
            img_path = WORKDIR.cache_dir / "res" / "default.jpg"
            return img_path
        except Exception as e:
            logger.opt(colors=True).warning(
                f"<y>Pusher</y>：获取默认图片失败，错误信息：{e}")
            return None

    def _clean_image_queue(self):
        url_dict = {}  # 存储图片url,key是url，value是数据源
        for item in self.image_queue:  # 遍历图片队列
            if CommonUtils.is_url(str(item)):
                if item not in url_dict:
                    url_dict[item] = "ANI_RSS"
                else:
                    continue
            else:
                # 如果不是url，则为emby的tag，需要转换为url
                if not FUNCTION.emby_enabled:
                    continue
                try:
                    url = EmbyUtils.splice_emby_image_url(
                        APPCONFIG.emby_host, self.emby_series_id, item)
                    if url not in url_dict:
                        url_dict[url] = "EMBY"
                    else:
                        continue
                except Exception as e:
                    logger.opt(colors=True).warning(
                        f"<y>Pusher</y>：获取emby图片失败，错误信息：{e}")
        return url_dict

    async def _download_first_valid_image(self, url_dict: dict):
        tasks = []  # 初始化任务列表
        errors = []  # 初始化错误列表
        binary = None  # 初始化结果
        for url, source in url_dict.items():
            try:
                if source == "ANI_RSS":
                    headers = {
                        "User-Agent": "AriadusTTT/nonebot_plugin_AniPush/1.0.0 (Python)"}
                    proxy = None
                elif source == "EMBY":
                    headers = {
                        "X-Emby-Token": APPCONFIG.emby_key,
                        "User-Agent": "AriadusTTT/nonebot_plugin_AniPush/1.0.0 (Python)"
                    }
                    proxy = APPCONFIG.proxy
                task = asyncio.create_task(
                    get_request(url, headers=headers, proxy=proxy, is_binary=True))
                tasks.append(task)
            except Exception as e:
                logger.opt(colors=True).warning(
                    f"<y>Pusher</y>：{url}下载任务创建失败，错误信息：{e}")
                continue
        if not tasks:  # 如果没有创建任何任务
            return None
        # 使用as_completed迭代处理
        for task in asyncio.as_completed(tasks):
            try:
                binary = await task
                for t in tasks:
                    if not t.done():
                        t.cancel()
                        try:
                            await t  # 等待取消完成
                        except (asyncio.CancelledError, Exception):
                            pass  # 预期中的异常，无需处理
                return binary  # 返回第一个成功的结果的二进制数据
            except Exception as e:
                errors.append(e)
        logger.opt(colors=True).warning(
            f"<y>Pusher</y>：图片下载全部失败，错误信息：{errors}")
        return None

    async def _save_bytes_to_cache(self, binary: bytes) -> Path | Literal[False]:
        if not WORKDIR.cache_dir:
            logger.opt(colors=True).warning(
                "<y>Pusher</y>：缓存目录缺失！")
            return False
        WORKDIR.cache_dir.mkdir(parents=True, exist_ok=True)
        img_path = WORKDIR.cache_dir / f"{self.tmdb_id}.png"
        try:
            temp_path = img_path.with_suffix('.tmp')
            temp_path.write_bytes(binary)
        except Exception as e:
            logger.opt(colors=True).warning(
                f"<y>Pusher</y>：图片写入失败，错误信息：{e}")
            return False
        try:
            shutil.move(temp_path, img_path)
        except Exception as e:
            logger.opt(colors=True).warning(
                f"<y>Pusher</y>：图片替换失败，错误信息：{e}")
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception as e:
                    logger.opt(colors=True).warning(
                        f"<y>Pusher</y>：临时图片删除失败，错误信息：{e}")
            return False
        return img_path
