import os
from logging import config as logging_config
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.logger import LOGGING

logging_config.dictConfig(LOGGING)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    PROJECT_NAME_FASTAPI: str = 'movies'

    ELASTIC_SCHEMA: str = 'http://'
    ELASTIC_HOST: str = '127.0.0.1'
    ELASTIC_PORT: int = 9200

    REDIS_HOST: str = '127.0.0.1'
    REDIS_PORT: int = 6379
    REDIS_PASSW: str | None = None

    ES_MAX_RETRIES: int = 3
    ES_REQUEST_TIMEOUT: int = 30

    REDIS_CONNECT_TIMEOUT: int = 5
    REDIS_SOCKET_TIMEOUT: int = 5

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_ignore_empty=True,
        extra='ignore',
    )


config = Settings()
