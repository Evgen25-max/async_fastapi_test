import logging
from functools import wraps

from elasticsearch.exceptions import ConnectionError as ESConnectionError, NotFoundError as ESNotFoundError, ConnectionTimeout
from redis.exceptions import RedisError
from services.custom_exceptions import FilmNotFoundError, FilmDataError, IndexNotFoundError

CUSTOM_EXCEPTIONS = (FilmNotFoundError, FilmDataError, IndexNotFoundError)

logger = logging.getLogger(__name__)


def handle_elastic_errors(func):
    """Обработка ошибок Elasticsearch."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except CUSTOM_EXCEPTIONS:
            raise
        except ESNotFoundError:
            raise
        except (ESConnectionError, ConnectionTimeout) as e:
            logger.error(
                'Elasticsearch недоступен при вызове %s: %s',
                func.__name__, e
            )
            raise
        except Exception as e:
            logger.exception(
                'Неожиданная ошибка в %s: %s',
                func.__name__, e
            )
            raise
    return wrapper


def handle_redis_errors(func):
    """Обработки ошибок Redis (не пробрасывает, возвращает None)."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except CUSTOM_EXCEPTIONS:
            raise
        except RedisError as e:
            logger.warning(
                'Redis недоступен при вызове %s: %s',
                func.__name__, e
            )
            return None
    return wrapper
