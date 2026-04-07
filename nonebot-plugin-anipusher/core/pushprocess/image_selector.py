#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片选择器模块 - 负责图片缓存管理与选择
主要功能包括：
- 从本地缓存中搜索图片
- 刷新图片缓存
- 图片有效性验证
- 提供降级策略（过期图片或默认图片）
"""
# 标准库
import asyncio
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
# 第三方库
from nonebot import logger
# 项目内部模块
from ...config import WORKDIR, APPCONFIG
from ...external import get_request
from ...exceptions import AppError


class ImageSelector:
    """
    图片选择器类 - 负责从本地缓存或网络获取图片并提供降级策略
    支持多种图片来源，包括本地缓存和网络下载，并提供完整的降级机制，
    确保在各种情况下都能提供可用的图片资源。
    """

    def __init__(self, image_queue: list, tmdb_id: str | None) -> None:
        """
        初始化图片选择器
        Args:
            image_queue: 图片URL队列，用于从网络获取图片
            tmdb_id: 媒体内容的TMDB ID，用于标识和缓存图片
        """
        self.image_queue = image_queue
        self.tmdb_id = tmdb_id
        self.output_img: Path | None = None

    async def select(self) -> Path | None:
        """
        选择并返回合适的图片路径
        优先级：有效本地缓存 -> 新下载图片 -> 过期缓存 -> 默认图片
        Returns:
            Path | None: 图片文件路径，当所有降级策略都失败时返回None
        """
        if not self.tmdb_id or self.tmdb_id == 'None':
            logger.opt(colors=True).warning(
                '<y>PUSHER</y>:无法验证图片缓存 —— TMDB ID 缺失')
            return self._fallback_to_available_image()
        # 先尝试从本地缓存中查找图片
        if self._search_in_localstore() and self.output_img is not None:
            # 如果本地缓存中找到图片，且图片有效，则直接返回
            logger.opt(colors=True).info(
                f'<g>PUSHER</g>:本地缓存图片 TMDB ID <c>{self.tmdb_id}</c> 已就绪')
            return self.output_img
        download_byte = await self._refresh_image_cache()
        if download_byte is None:
            return self._fallback_to_available_image()
        # 保存图片到本地缓存
        try:
            if not WORKDIR.cache_dir:
                AppError.ResourceNotFound.raise_('项目缓存目录缺失')
            local_img: Path = WORKDIR.cache_dir / f"{self.tmdb_id}.jpg"
            with open(local_img, 'wb') as f:
                f.write(download_byte)
            self.output_img = local_img
            logger.opt(colors=True).info(
                f'<g>PUSHER</g>:TMDB ID <c>{self.tmdb_id}</c> 图片缓存更新成功')
            return self.output_img
        except Exception as e:
            logger.opt(colors=True).error(
                f'<y>PUSHER</y>:保存图片到本地缓存 <c>{local_img}</c> 失败 —— {e}')
            return self._fallback_to_available_image()

    def _search_in_localstore(self) -> bool:
        """
        在本地缓存中搜索有效的图片
        Returns:
            bool: 是否找到有效的本地缓存图片
        """
        try:
            if not WORKDIR.cache_dir:
                raise AppError.ResourceNotFound.raise_('项目缓存目录缺失')
            local_img: Path = WORKDIR.cache_dir / f"{self.tmdb_id}.jpg"
            if local_img.exists() and self._is_image_valid(local_img):
                self.output_img = local_img
                return True
            return False
        except Exception as e:
            logger.opt(colors=True).error(
                f'<y>PUSHER</y>:本地缓存图片搜索 <r>异常</r> —— {e}')
            return False

    def _fallback_to_available_image(self) -> Path | None:
        """
        回退到可用图片（过期图片或默认图片）
        当无法获取新图片时，依次尝试使用：
        1. 已存在但可能过期的图片
        2. 默认图片
        Returns:
            Path | None: 可用图片路径，若所有降级策略失败则返回None
        """
        if self.output_img:
            logger.opt(colors=True).warning(
                '<y>PUSHER</y>:更新图片 <r>失败</r>，回退使用超期图片')
            return self.output_img
        logger.opt(colors=True).warning('<y>PUSHER</y>:无可用图片，回退至默认图片')
        try:
            if not WORKDIR.cache_dir:
                raise AppError.ResourceNotFound.raise_('项目缓存目录缺失')
            default_img: Path = WORKDIR.cache_dir / "default_img.png"
            if not default_img.exists():
                raise AppError.ResourceNotFound.raise_('默认图片资源缺失')
            return default_img
        except Exception as e:
            logger.opt(colors=True).error(
                f'<y>PUSHER</y>:获取默认图片 <r>失败</r> —— {e}')
            return None

    async def _refresh_image_cache(self) -> bytes | None:
        """
        刷新图片缓存，从网络下载新图片
        Returns:
            bytes | None: 下载的图片字节数据，失败时返回None
        """
        try:
            if not WORKDIR.cache_dir:
                raise AppError.ResourceNotFound.raise_('项目缓存目录缺失')
            # 确保缓存目录存在
            WORKDIR.cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.opt(colors=True).error(
                f'<y>PUSHER</y>:刷新图片缓存初始化 <r>失败</r> —— {e}')
            return None
        # 创建并发任务列表
        tasks = []
        for img_url in self.image_queue:
            try:
                task = self._create_image_task(img_url)
                if task:
                    tasks.append(task)
            except Exception as e:
                logger.opt(colors=True).error(
                    f'<y>PUSHER</y>:创建图片下载任务 <c>{img_url}</c> 失败 —— {e}')
                continue
        if not tasks:
            logger.opt(colors=True).warning(
                f'<y>PUSHER</y>:TMDB ID <c>{self.tmdb_id}</c> 无有效图片 URL')
            return None
        # 等待第一个完成的任务
        return await self._wait_first_completed_task(tasks)

    def _create_image_task(self, img_url: str) -> asyncio.Task:
        """
        创建图片下载任务
        Args:
            img_url: 图片URL
        Returns:
            asyncio.Task: 图片下载任务对象
        Raises:
            AppError.ImageDownloadTaskError: 创建任务失败时抛出
        """
        try:
            if "bgm.tv" in img_url:
                headers = {
                    "User-Agent": "AriadusTTT/nonebot_plugin_AniPush/1.0.0 (Python)"}
                proxy = None
            else:
                headers = {
                    "X-Emby-Token": APPCONFIG.emby_key,
                    "User-Agent": "AriadusTTT/nonebot_plugin_AniPush/1.0.0 (Python)"}
                proxy = APPCONFIG.proxy
            task = asyncio.create_task(
                get_request(
                    img_url,
                    headers=headers,
                    proxy=proxy,
                    is_binary=True,
                    timeout=aiohttp.ClientTimeout(
                        total=15,
                        connect=5,
                        sock_read=10
                    ),
                )
            )
            return task
        except Exception as e:
            AppError.ImageDownloadTaskError.raise_(f"创建图片下载任务失败: {str(e)}")

    async def _wait_first_completed_task(self, tasks: list[asyncio.Task]) -> bytes | None:
        """
        等待第一个成功完成的任务，并取消剩余任务
        Args:
            tasks: 任务列表
        Returns:
            bytes | None: 第一个成功任务的结果，所有任务失败时返回None
        """
        remaining_tasks = set(tasks)
        while remaining_tasks:
            done, pending = await asyncio.wait(remaining_tasks, return_when=asyncio.FIRST_COMPLETED)
            remaining_tasks -= done
            for task in done:
                if not task.cancelled():
                    try:
                        result = task.result()
                        for t in pending:
                            t.cancel()
                        if pending:
                            await asyncio.wait(pending, timeout=1.0)  # 等待取消完成
                        return result
                    except Exception as e:
                        logger.opt(colors=True).error(
                            f'<y>PUSHER</y>:图片下载 <r>失败</r>  —— {e}')
        logger.opt(colors=True).error(
            f'<y>PUSHER</y>:TMDB ID <c>{self.tmdb_id}</c> 所有图片下载任务 <r>失败</r>')
        return None

    @staticmethod
    def _is_image_valid(img_path: str | Path, expire_hours: float = 14 * 24) -> bool:
        """
        检查图片是否有效（未过期）
        Args:
            img_path: 图片路径
            expire_hours: 图片过期时间（小时），默认14天
        Returns:
            bool: 图片是否有效（存在且未过期）
        """
        try:
            img_path = Path(img_path)
            if not img_path.exists():
                return False
            modified_time = datetime.fromtimestamp(img_path.stat().st_mtime)
            time_diff = datetime.now() - modified_time
            return time_diff < timedelta(hours=expire_hours)
        except Exception as e:
            logger.opt(colors=True).error(
                f'<y>PUSHER</y>:检查本地缓存图片有效期 <r>失败</r> —— {e}')
            return False
