import json
import logging
from typing import Optional

from pydantic import ValidationError
from redis.asyncio import Redis

from api.const import FILM_CACHE_EXPIRE_IN_SECONDS
from models.film import Film
from cache.abc_cache import FilmCache
from services.exception_handler import handle_redis_errors

logger = logging.getLogger(__name__)


class RedisFilmCache(FilmCache):
    """Реализация кэша на Redis."""

    def __init__(self, redis: Redis):
        self._redis = redis

    @handle_redis_errors
    async def get_film(self, film_id: str) -> Optional[Film]:
        data = await self._redis.get(film_id)
        if not data:
            return None
        try:
            return Film.model_validate_json(data)
        except ValidationError:
            logger.warning('Повреждённые данные в кеше для фильма %s', film_id)
            return None

    @handle_redis_errors
    async def put_film(self, film: Film) -> None:
        await self._redis.set(
            film.id,
            film.model_dump_json(),
            FILM_CACHE_EXPIRE_IN_SECONDS,
        )

    @handle_redis_errors
    async def get_films_list(self, cache_key: str) -> Optional[list[Film]]:
        data = await self._redis.get(cache_key)
        if not data:
            return None
        try:
            films_data = json.loads(data)
            return [Film.model_validate(film_dict) for film_dict in films_data]
        except (json.JSONDecodeError, ValidationError):
            logger.warning('Повреждённые данные в кеше для ключа %s', cache_key)
            return None

    @handle_redis_errors
    async def put_films_list(self, cache_key: str, films: list[Film]) -> None:
        films_data = [film.model_dump() for film in films]
        await self._redis.set(
            cache_key,
            json.dumps(films_data),
            FILM_CACHE_EXPIRE_IN_SECONDS,
        )
