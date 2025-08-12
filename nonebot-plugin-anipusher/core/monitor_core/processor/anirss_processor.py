
import json
import re
from nonebot import logger
from ..abstract_processor import AbstractDataProcessor
from ....database import DatabaseTables
from ....exceptions import AppError
from ....utils import CommonUtils


@AbstractDataProcessor.register(DatabaseTables.TableName.ANI_RSS)
class AniRSSProcessor(AbstractDataProcessor):
    """AniRSS数据处理器"""

    async def _reformat(self):
        try:
            default_dict = DatabaseTables.generate_default_schema(
                self.source)
        except Exception as e:
            raise AppError.Exception(
                AppError.UnknownError, f"{self.source.value}：获取默认模板结构异常：{e}")
        if not self.raw_data:
            raise AppError.Exception(
                AppError.ParamNotFound, f"{self.source.value}：待处理的数据为空")
        if not isinstance(self.raw_data, dict):
            raise AppError.Exception(
                AppError.UnSupportedType, f"{self.source.value}：待处理的数据类型错误：{type(self.raw_data)}")
        try:
            extract = self.DataExtraction(self.raw_data)  # 初始化数据提取类
            send_status = False  # 配置默认发送状态
            timestamp = extract.extract_timestamp()  # 提取时间戳
            action = extract.extract_action()  # 提取动作
            title = extract.extract_title()  # 提取标题
            jp_title = extract.extract_jp_title()  # 提取日文标题
            tmdb_title = extract.extract_tmdb_title()  # 提取TMDB标题
            score = extract.extract_score()  # 提取评分
            tmdb_id = extract.extract_tmdb_id()  # 提取TMDB ID
            tmdb_url = extract.extract_tmdb_url()  # 提取TMDB链接
            bangumi_url = extract.extract_bgm_url()  # 提取Bangumi链接
            season = extract.extract_season()  # 提取季度
            episode = extract.extract_episode()  # 提取集数
            tmdb_episode_title = extract.extract_episodeTitle()  # 提取TMDB集标题
            bangumi_episode_title = extract.extract_bgmEpisodeTitle()  # 提取Bangumi集标题
            bangumi_jpepisode_title = extract.extract_bgmJpEpisodeTitle()  # 提取Bangumi日文集标题
            subgroup = extract.extract_subgroup()  # 提取字幕组
            progress = extract.extract_progress()  # 提取进度
            premiere = extract.extract_premiere()  # 提取首播日期
            download_path = extract.extract_download_path()  # 提取下载路径
            text = extract.extract_text()  # 提取文本内容
            image = extract.extract_image_url()  # 提取图片链接
            raw_data = extract.extract_raw_data()  # 提取原始数据
        except (AppError.Exception, Exception) as e:
            raise AppError.Exception(
                AppError.UnknownError, f"{self.source.value}：数据格式化异常：{e}")
        default_dict.update({
            "send_status": send_status,
            "timestamp": timestamp,
            "action": action,
            "title": title,
            "jp_title": jp_title,
            "tmdb_title": tmdb_title,
            "score": score,
            "tmdb_id": tmdb_id,
            "tmdb_url": tmdb_url,
            "bangumi_url": bangumi_url,
            "season": season,
            "episode": episode,
            "tmdb_episode_title": tmdb_episode_title,
            "bangumi_episode_title": bangumi_episode_title,
            "bangumi_jpepisode_title": bangumi_jpepisode_title,
            "subgroup": subgroup,
            "progress": progress,
            "premiere": premiere,
            "download_path": download_path,
            "text": text,
            "image_url": image,
            "raw_data": raw_data
        })
        self.reformated_data = default_dict
        self.tmdb_id = tmdb_id
        logger.opt(colors=True).info(
            f"<g>{self.source.value}</g>：数据整形化 <g>完成</g>，等待数据持久化")

    class DataExtraction:
        def __init__(self, data: dict):
            self.data = data

        def extract_timestamp(self) -> str:
            return CommonUtils.get_timestamp()

        def extract_action(self) -> str | None:
            return self.data.get("action")

        # 去除标题中的TMDB ID
        def extract_title(self) -> str | None:
            title = self.data.get("title")
            if not title:
                return None
            return re.sub(r'\[tmdbid=\d+\]', '', str(title)).strip()

        def extract_jp_title(self) -> str | None:
            return self.data.get("jpTitle")

        def extract_score(self) -> str | None:
            return self.data.get("score")

        def extract_tmdb_title(self) -> str | None:
            return self.data.get("themoviedbName")

        def extract_tmdb_id(self) -> int | None:
            return self.data.get("tmdbid")

        def extract_tmdb_url(self) -> str | None:
            return self.data.get("tmdbUrl")

        def extract_bgm_url(self) -> str | None:
            return self.data.get("bgmUrl")

        def extract_season(self) -> str | None:
            return self.data.get("season")

        def extract_episode(self) -> str | None:
            return self.data.get("episode")

        def extract_subgroup(self) -> str | None:
            return self.data.get("subgroup")

        def extract_progress(self) -> str | None:
            return self.data.get("progress")

        def extract_premiere(self) -> str | None:
            return self.data.get("premiere")

        def extract_text(self) -> str | None:
            return self.data.get("text")

        def extract_download_path(self) -> str | None:
            return self.data.get("downloadPath")

        def extract_episodeTitle(self) -> str | None:
            return self.data.get("episodeTitle")

        def extract_bgmEpisodeTitle(self) -> str | None:
            return self.data.get("bgmEpisodeTitle")

        def extract_bgmJpEpisodeTitle(self) -> str | None:
            return self.data.get("bgmJpEpisodeTitle")

        def extract_image_url(self) -> str | None:
            return self.data.get("image")

        def extract_raw_data(self) -> str | None:
            return json.dumps(self.data, ensure_ascii=False)

    def _enable_anime_process(self):
        """
        可选项，启用Anime数据处理
        这里可以根据实际需求决定是否启用Anime数据处理
        """
        return True
