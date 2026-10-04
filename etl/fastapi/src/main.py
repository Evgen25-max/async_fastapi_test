import logging
import logging.config
from contextlib import asynccontextmanager
from core.config import config
from elasticsearch import ConnectionTimeout
from elasticsearch.exceptions import ConnectionError as ESConnectionError
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from services.custom_exceptions import FilmNotFoundError, FilmDataError, IndexNotFoundError
from api.v1 import films
from cache.redis_film import RedisFilmCache
from core.logger import LOGGING
from db import elastic, redis
from db_work.elastic_film import ElasticFilmRepository
from services.film import FilmService


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
        logger.info('Elasticsearch доступен')
    except Exception as e:
        logger.warning('Elasticsearch недоступен при старте: %s', e)

    app.state.film_service = FilmService(
        cache=RedisFilmCache(redis.get_redis()),
        repository=ElasticFilmRepository(elastic.get_elastic()),
    )

    logger.info('Приложение запущено')
    try:
        yield
    finally:
        logger.info('Остановка приложения')
        try:
            await redis.close_redis()
        except Exception as e:
            logger.error('Ошибка при закрытии Redis: %s', e)
        try:
            await elastic.close_elastic()
        except Exception as e:
            logger.error('Ошибка при закрытии Elasticsearch: %s', e)

        logger.info('Попытка закрытия подключений завершена')


app = FastAPI(
    title=config.PROJECT_NAME_FASTAPI,
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
    lifespan=lifespan,
)


# --- Централизованные обработчики исключений ---

@app.exception_handler(FilmNotFoundError)
async def film_not_found_handler(request: Request, exc: FilmNotFoundError):
    """Обработчик: фильм не найден → 404."""
    return JSONResponse(
        status_code=404,
        content={'detail': f'Фильм {exc.film_id} не найден'},
    )


@app.exception_handler(FilmDataError)
async def film_data_corrupted_handler(request: Request, exc: FilmDataError):
    '''Обработчик: данные фильма повреждены → 500.'''
    logger.exception('Повреждённые данные фильма %s: %s', exc.film_id, exc)
    return JSONResponse(
        status_code=500,
        content={'detail': f'Данные фильма повреждены {exc.film_id}'},
    )


@app.exception_handler(ESConnectionError)
async def es_connection_error_handler(
    request: Request, exc: ESConnectionError
      ):
    logger.exception('Elasticsearch недоступен: %s', exc)
    return JSONResponse(
        status_code=503,
        content={
            'detail': 'Сервис недоступен. Попробуйте позднее.',
        },
    )


@app.exception_handler(ConnectionTimeout)
async def es_timeout_error_handler(request: Request, exc: ConnectionTimeout):
    logger.exception('Превышено время ожидания ответа от Elasticsearch: %s', exc)
    return JSONResponse(
        status_code=503,
        content={
            'detail': 'Сервис недоступен. Попробуйте позднее.',
        },
    )


@app.exception_handler(IndexNotFoundError)
async def index_not_found_handler(request: Request, exc: IndexNotFoundError):
    logger.exception('Хранилище недоступно: индекс %s не найден', exc.index_name)
    return JSONResponse(
        status_code=503,
        content={'detail': 'Сервис временно недоступен. Попробуйте позднее.'},
    )

app.include_router(films.router, prefix='/api/v1/films', tags=['films'])
