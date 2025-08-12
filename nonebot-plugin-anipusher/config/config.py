from os import path
from pydantic import BaseModel


class AnipushConfig(BaseModel):
    emby_host: str = "Basic"
    emby_apikey: str = "Basic"
    tmdb_apikey: str = "Basic"
    tmdb_proxy: str = "Basic"


class Config(BaseModel):
    anipush: AnipushConfig
