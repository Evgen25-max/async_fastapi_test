import json
import logging
from functools import lru_cache
from typing import Optional

from api.const import FILM_CACHE_EXPIRE_IN_SECONDS
from api.filters import FilmFilter
from db.elastic import get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch
from elasticsearch import ConnectionError as ESConnectionError
from fastapi import Depends
from models.film import Film
from pydantic import ValidationError
from redis.asyncio import Redis
from redis.exceptions import RedisError

from services.exception_handler import (handle_elastic_errors,
                                        handle_redis_errors)

logger = logging.getLogger(__name__)


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_all(
            self,
            offset: int,
            page_size: int,
            sort_by: list,
            filters: FilmFilter,
            include_fields: set[str],
    ) -> list[Film]:
        sort_str = json.dumps(sort_by, sort_keys=True)
        filters_str = json.dumps(
            filters.model_dump(exclude_none=True), sort_keys=True
            )
        include_fields_str = json.dumps(sorted(list(include_fields)))
        cache_key = f"films_list:{offset}:{page_size}:{sort_str}:{filters_str}:{include_fields_str}"
        cached_films = await self._get_films_list_from_cache(cache_key)
        if cached_films is not None:
            return [
                Film.model_validate(film_dict) for film_dict in cached_films
                ]

        films = await self._get_films_from_elastic(
            offset=offset,
            page_size=page_size,
            sort_by=sort_by,
            filters=filters,
            )

        await self._put_films_list_to_cache(cache_key, films)
        return films

    @handle_redis_errors
    async def _get_films_list_from_cache(self, cache_key: str) -> Optional[list[dict]]:
        try:
            data = await self.redis.get(cache_key)
        except RedisError as e:
            logger.warning('Redis недоступен при поиске списка фильмов: %s', e)
            return None
        if not data:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            logger.warning('Повреждённые данные в кеше для ключа %s', cache_key)
            return None

    async def get_by_id(self, film_id: str) -> Optional[Film]:
        film = await self._film_from_cache(film_id)
        if not film:
            film = await self._get_film_from_elastic(film_id)
            if not film:
                return None
            await self._put_film_to_cache(film)

        return film

    @handle_elastic_errors
    async def _get_film_from_elastic(self, film_id: str) -> Optional[Film]:
        doc = await self.elastic.get(index='movies', id=film_id)
        try:
            return Film(**doc['_source'])
        except (ValidationError, KeyError):
            logger.exception('Битые данные в ES для фильма %s', film_id)
            raise

    @handle_elastic_errors
    async def _get_films_from_elastic(
        self,
        offset: int,
        page_size: int,
        sort_by: list,
        filters: FilmFilter,
    ) -> list[Film]:
        must_conditions = []
        filter_all = []
        if filters.has_any_filter():
            text_filters = {
                'title': filters.title,
                'description': filters.description,
                'directors_names': filters.directors_names,
                'writers_names': filters.writers_names,
                'actors_names': filters.actors_names,
            }

            must_conditions = [
                {
                    'match': {
                        field: {
                            'query': value,
                            'fuzziness': 'AUTO',
                            'operator': 'and',
                        }
                    }
                }
                for field, value in text_filters.items() if value
            ]
            if filters.imdb_rating_from is not None or filters.imdb_rating_to is not None:
                range_condition = {}
                if filters.imdb_rating_from is not None:
                    range_condition['gte'] = filters.imdb_rating_from
                if filters.imdb_rating_to is not None:
                    range_condition['lte'] = filters.imdb_rating_to
                filter_all.append({'range': {'imdb_rating': range_condition}})

        if must_conditions or filter_all:
            query = {'bool': {}}

            if must_conditions:
                query['bool']['must'] = must_conditions

            if filter_all:
                query['bool']['filter'] = filter_all
        else:
            query = {'match_all': {}}
        search_params = {
            'index': 'movies',
            'query': query,
            'sort': sort_by,
            'from_': offset,
            'size': page_size,
        }
        docs = await self.elastic.search(**search_params)
        films = [Film(**doc['_source']) for doc in docs['hits']['hits']]
        return films

    @handle_redis_errors
    async def _film_from_cache(self, film_id: str) -> Optional[Film]:
        try:
            data = await self.redis.get(film_id)
        except RedisError as e:
            logger.warning('Redis недоступен при поиске фильма %s: %s', film_id, e)
            return None
        if not data:
            return None
        try:
            film = Film.model_validate_json(data)
        except ValidationError as e:
            logger.warning(
                'Повреждённые данные в кеше для фильма %s: %s', film_id, e
                )
            return None
        return film

    @handle_redis_errors
    async def _put_film_to_cache(self, film: Film):
        try:
            await self.redis.set(film.id, film.model_dump_json(), FILM_CACHE_EXPIRE_IN_SECONDS)
        except RedisError as e:
            logger.warning("Redis недоступен при сохранении фильма %s: %s", film.id, e)

    @handle_redis_errors
    async def _put_films_list_to_cache(self, cache_key: str, films: list[Film]):
        try:
            films_data = [film.model_dump() for film in films]
            await self.redis.set(
                cache_key,
                json.dumps(films_data),
                FILM_CACHE_EXPIRE_IN_SECONDS
            )
        except RedisError as e:
            logger.warning('Redis недоступен при сохранении списка фильмов: %s', e)

@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
