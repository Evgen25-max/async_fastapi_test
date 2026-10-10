import json
import logging
from functools import lru_cache
from typing import Optional
from api.const import MAX_OFFSET
from fastapi import Depends, HTTPException

from api.filters import FilmFilter
from cache.abc_cache import FilmCache
from cache.redis_film import RedisFilmCache
from db.elastic import get_elastic
from db.redis import get_redis
from models.film import Film
from db_work.abc_film import FilmRepository
from db_work.elastic_film import ElasticFilmRepository
from services.custom_exceptions import FilmNotFoundError

logger = logging.getLogger(__name__)


class FilmService:
    """
    Бизнес-логика между кэшем и хранилищем.
    """

    def __init__(self, cache: FilmCache, repository: FilmRepository):
        self._cache = cache
        self._repository = repository

    async def get_all(
        self,
        page: int,
        page_size: int,
        sort_field: str,
        sort_order: str,
        filters: FilmFilter,
    ) -> list[Film]:
        offset = (page - 1) * page_size
        if offset + page_size > MAX_OFFSET:
            raise HTTPException(
                status_code=400,
                detail='Слишком глубокая страница. '
                'Используйте фильтры для уточнения запроса.'
            )

        cache_key = self._get_cache_key(
            offset, page_size, sort_field, sort_order, filters
        )

        cached_films = await self._cache.get_films_list(cache_key)
        if cached_films is not None:
            return cached_films

        films = await self._repository.get_all(
            offset=offset,
            page_size=page_size,
            sort_field=sort_field,
            sort_order=sort_order,
            filters=filters,
        )

        await self._cache.put_films_list(cache_key, films)
        return films

    async def get_by_id(self, film_id: str) -> Optional[Film]:
        film = await self._cache.get_film(film_id)
        if film is not None:
            return film

        film = await self._repository.get_by_id(film_id)
        if film is None:
            raise FilmNotFoundError(film_id)

        await self._cache.put_film(film)
        return film

    def _get_cache_key(
        self,
        offset: int,
        page_size: int,
        sort_field: str,
        sort_order: str,
        filters: FilmFilter,
    ) -> str:
        sort_str = json.dumps({"field": sort_field, "order": sort_order}, sort_keys=True)
        filters_str = json.dumps(filters.model_dump(exclude_none=True), sort_keys=True)
        return f'films_list:{offset}:{page_size}:{sort_str}:{filters_str}'


@lru_cache()
def get_film_service(
    redis=Depends(get_redis),
    elastic=Depends(get_elastic),
) -> FilmService:
    """Cвязывает реализации с абстракциями."""
    cache = RedisFilmCache(redis)
    repository = ElasticFilmRepository(elastic)
    return FilmService(cache=cache, repository=repository)
