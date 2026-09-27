import logging
from functools import wraps

from elasticsearch import ConnectionTimeout, NotFoundError
from elasticsearch.exceptions import ConnectionError as ESConnectionError
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


def handle_elastic_errors(func):
    """Обработка ошибок Elasticsearch."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except NotFoundError:
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
        except RedisError as e:
            logger.warning(
                'Redis недоступен при вызове %s: %s',
                func.__name__, e
            )
            return None
    return wrapper