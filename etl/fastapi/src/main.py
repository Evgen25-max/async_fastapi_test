import logging
import logging.config
from contextlib import asynccontextmanager

from elasticsearch import ConnectionTimeout
from elasticsearch.exceptions import ConnectionError as ESConnectionError
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.v1 import films
from core.config import config
from core.logger import LOGGING
from db import elastic, redis

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Запуск приложения %s...', config.PROJECT_NAME_FASTAPI)
    redis.init_redis()
    elastic.init_elastic()

    try:
        await redis.get_redis().ping()
        logger.info('Redis доступен')
    except Exception as e:
        logger.warning('Redis недоступен при старте: %s', e)

    try:
        await elastic.get_elastic().info()
        logger.info("Elasticsearch доступен")
    except Exception as e:
        logger.warning('Elasticsearch недоступен при старте: %s', e)

    logger.info('Приложение запущено')

    yield
    logger.info('Остановка приложения')
    await redis.close_redis()
    await elastic.close_elastic()
    logger.info('Подключения закрыты')


app = FastAPI(
    title=config.PROJECT_NAME_FASTAPI,
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
    lifespan=lifespan,
)


@app.exception_handler(ESConnectionError)
async def es_connection_error_handler(
    request: Request, exc: ESConnectionError
      ):
    logger.error('Elasticsearch недоступен: %s', exc)
    return JSONResponse(
        status_code=503,
        content={
            'detail': 'Сервис недоступен. Попробуйте позднее.',
        },
    )


@app.exception_handler(ConnectionTimeout)
async def es_timeout_error_handler(request: Request, exc: ConnectionTimeout):
    logger.error('Превышено время ожидания ответа от Elasticsearch: %s', exc)
    return JSONResponse(
        status_code=503,
        content={
            'detail': 'Сервис недоступен. Попробуйте позднее.',
        },
    )

app.include_router(films.router, prefix='/api/v1/films', tags=['films'])
