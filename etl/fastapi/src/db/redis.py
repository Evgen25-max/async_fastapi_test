from typing import Optional

from core.config import config

from redis.asyncio import Redis

redis: Optional[Redis] = None


def init_redis() -> None:
    """Инициализирует клиент."""
    global redis
    redis = Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        password=config.REDIS_PASSW,
        socket_connect_timeout=config.REDIS_CONNECT_TIMEOUT,
        socket_timeout=config.REDIS_SOCKET_TIMEOUT,
    )


async def close_redis() -> None:
    """Закрывает клиент."""
    global redis
    if redis is not None:
        await redis.close()
        redis = None


def get_redis() -> Redis:
    """Возвращает клиент."""
    if redis is None:
        raise RuntimeError(
            'Redis не инициализирован. Вызовите init_redis() при старте.'
        )
    return redis
