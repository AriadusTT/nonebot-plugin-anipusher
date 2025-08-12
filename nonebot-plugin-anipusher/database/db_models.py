from enum import Enum
from typing import TypedDict, Union, Literal, NotRequired


class DatabaseTables:
    """集中管理所有表结构和枚举"""

    class TableName(str, Enum):
        """表名枚举"""
        EMBY = "EMBY"
        ANI_RSS = "ANIRSS"
        ANIME = "ANIME"

    class ColumnDef(TypedDict):
        type: Literal["INTEGER", "TEXT", "REAL", "BLOB"]
        required: bool
        default: Union[int, str, None]  # 允许int类型
        primary_key: NotRequired[bool]  # 主键可选
        auto_increment: NotRequired[bool]  # 自增可选
        allowed_values: NotRequired[list[Union[int, str]]]  # 允许值可选

    # 表结构定义
    SCHEMAS: dict[TableName, dict[str, ColumnDef]] = {
        TableName.EMBY: {
            # 系统字段↓
            'id': {'type': 'INTEGER', 'required': False, 'default': None, 'primary_key': True, 'auto_increment': True},
            'send_status': {'type': 'INTEGER', 'required': True, 'default': 0, 'allowed_values': [0, 1]},
            'timestamp': {'type': 'TEXT', 'required': False, 'default': None},
            # 剧集信息字段↓
            'type': {'type': 'TEXT', 'required': False, 'default': None},
            'title': {'type': 'TEXT', 'required': False, 'default': None},
            # 建议获取item下的overview
            'description': {'type': 'TEXT', 'required': False, 'default': None},
            'season': {'type': 'INTEGER', 'required': False, 'default': None},
            'episode': {'type': 'INTEGER', 'required': False, 'default': None},
            'episode_title': {'type': 'TEXT', 'required': False, 'default': None},
            # 外部ID字段↓
            'tmdb_id': {'type': 'INTEGER', 'required': False, 'default': None},
            'imdb_id': {'type': 'TEXT', 'required': False, 'default': None},
            'tvdb_id': {'type': 'INTEGER', 'required': False, 'default': None},
            # 内部ID字段↓
            # 剧集ID
            'series_id': {'type': 'INTEGER', 'required': False, 'default': None},
            # 季度ID
            'season_id': {'type': 'INTEGER', 'required': False, 'default': None},
            # 单集ID
            'episode_id': {'type': 'INTEGER', 'required': False, 'default': None},
            # 电视剧海报
            # 系列海报
            'series_tag': {'type': 'TEXT', 'required': False, 'default': None},
            # 季度海报
            # 预留字段（如需）
            "season_tag": {"type": "TEXT", "required": False, 'default': None},
            # 单集海报
            # 预留字段（如需）
            'episode_tag': {'type': 'TEXT', 'required': False, 'default': None},
            # Emby服务器信息字段↓
            'server_name': {'type': 'TEXT', 'required': False, 'default': None},
            'server_id': {'type': 'TEXT', 'required': False, 'default': None},
            # type为series时，表示合并的剧集数量
            'merged_episode': {'type': 'INTEGER', 'required': False, 'default': None},
            # 原始数据字段↓
            'raw_data': {'type': 'TEXT', 'required': False, 'default': None}
        },
        TableName.ANI_RSS: {
            # 系统字段↓
            'id': {'type': 'INTEGER', 'required': False, 'default': None, 'primary_key': True, 'auto_increment': True},
            'send_status': {'type': 'INTEGER', 'required': True, 'default': 0, 'allowed_values': [0, 1]},
            'timestamp': {'type': 'TEXT', 'required': False, 'default': None},
            # 剧集信息字段↓(通过AniRSS webhook获取)
            # ani-rss动作
            'action': {'type': 'TEXT', 'required': False, 'default': None},
            'title': {'type': 'TEXT', 'required': False, 'default': None},  # 标题
            # BGM日文标题
            'jp_title': {'type': 'TEXT', 'required': False, 'default': None},
            # BGM英文标题
            'tmdb_title': {'type': 'TEXT', 'required': False, 'default': None},
            'score': {'type': 'REAL', 'required': False, 'default': None},  # 评分
            # TMDBID
            'tmdb_id': {'type': 'INTEGER', 'required': False, 'default': None},
            # TMDB链接
            'tmdb_url': {'type': 'TEXT', 'required': False, 'default': None},
            # Bangumi链接
            'bangumi_url': {'type': 'TEXT', 'required': False, 'default': None},
            # 季度
            'season': {'type': 'INTEGER', 'required': False, 'default': None},
            # 集数
            'episode': {'type': 'INTEGER', 'required': False, 'default': None},
            # Tmdb集标题
            'tmdb_episode_title': {'type': 'TEXT', 'required': False, 'default': None},
            # Bangumi集标题
            'bangumi_episode_title': {'type': 'TEXT', 'required': False, 'default': None},
            # 集标题
            'bangumi_jpepisode_title': {'type': 'TEXT', 'required': False, 'default': None},
            # 字幕组
            'subgroup': {'type': 'TEXT', 'required': False, 'default': None},
            # 进度
            'progress': {'type': 'TEXT', 'required': False, 'default': None},
            # 首播日期
            'premiere': {'type': 'TEXT', 'required': False, 'default': None},
            # 下载路径
            'download_path': {'type': 'TEXT', 'required': False, 'default': None},
            'text': {'type': 'TEXT', 'required': False, 'default': None},  # 文本
            # 图片链接
            'image_url': {'type': 'TEXT', 'required': False, 'default': None},
            # 原始数据字段↓
            'raw_data': {'type': 'TEXT', 'required': False, 'default': None}
        },
        TableName.ANIME: {
            'tmdb_id': {'type': 'INTEGER', 'required': False, 'default': None, 'primary_key': True},
            'emby_title': {'type': 'TEXT', 'required': False, 'default': None},
            'tmdb_title': {'type': 'TEXT', 'required': False, 'default': None},
            'score': {'type': 'REAL', 'required': False, 'default': None},
            'tmdb_url': {'type': 'TEXT', 'required': False, 'default': None},
            'bangumi_url': {'type': 'TEXT', 'required': False, 'default': None},
            'ani_rss_image': {'type': 'TEXT', 'required': False, 'default': None},
            'emby_series_tag': {'type': 'TEXT', 'required': False, 'default': None},
            'emby_series_url': {'type': 'TEXT', 'required': False, 'default': None},
            # 群组订阅者
            'group_subscriber': {'type': 'TEXT', 'required': False, 'default': "{}"},
            # 私信订阅者
            'private_subscriber': {'type': 'TEXT', 'required': False, 'default': "[]"}
        }
    }

    @classmethod
    def get_table_schema(cls, table_name: TableName) -> dict[str, ColumnDef]:
        """
        获取指定表的结构定义
        Args:
            table_name: 表名枚举
        Returns:
            表的结构定义字典
        """
        return cls.SCHEMAS[table_name]

    @classmethod
    def get_table_names(cls) -> list['DatabaseTables.TableName']:
        """
        获取所有表名
        Returns:
            所有表名的列表
        """
        return list(cls.TableName)

    @classmethod
    def generate_default_schema(cls, table_name: TableName) -> dict[str, object]:
        """
        生成默认值字典
        Args:
            table_name: 表名枚举
        Returns:
            默认值字典
        """

        default_dict = {}
        if table_name not in cls.SCHEMAS:
            raise ValueError(f"默认结构表{table_name}不存在")
        for column_name, column_def in cls.SCHEMAS[table_name].items():
            default_value = column_def.get('default', None)
            default_dict[column_name] = default_value
        return default_dict
