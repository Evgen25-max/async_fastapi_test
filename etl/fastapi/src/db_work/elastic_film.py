import logging
from typing import Optional

from elasticsearch import AsyncElasticsearch
from pydantic import ValidationError

from api.filters import FilmFilter
from models.film import Film
from db_work.abc_film import FilmRepository
from services.exception_handler import handle_elastic_errors
from services.custom_exceptions import FilmNotFoundError, FilmDataError, IndexNotFoundError
from elasticsearch import NotFoundError as ESNotFoundError

logger = logging.getLogger(__name__)

MOVIES_INDEX = 'movies'


class ElasticFilmRepository(FilmRepository):
    """Реализация хранилища на Elasticsearch."""

    def __init__(self, elastic: AsyncElasticsearch):
        self._elastic = elastic

    def _handle_not_found(
        self, exc: ESNotFoundError, film_id: str | None = None
    ) -> None:
        """Различает отсутствие индекса и отсутствие документа."""
        error_type = (exc.body or {}).get('error', {}).get('type', '')

        if error_type == 'index_not_found_exception':
            logger.error('Индекс %s не найден в Elasticsearch', MOVIES_INDEX)
            raise IndexNotFoundError(MOVIES_INDEX) from exc
        if film_id is not None:
            raise FilmNotFoundError(film_id) from exc
        raise exc

    @handle_elastic_errors
    async def get_by_id(self, film_id: str) -> Optional[Film]:
        try:
            doc = await self._elastic.get(index=MOVIES_INDEX, id=film_id)
        except ESNotFoundError as e:
            self._handle_not_found(e, film_id)
        try:
            return Film(**doc['_source'])
        except (ValidationError, KeyError):
            logger.exception('Битые данные в ES для фильма %s', film_id)
            raise FilmDataError(film_id)

    @handle_elastic_errors
    async def get_all(
        self,
        offset: int,
        page_size: int,
        sort_field: str,
        sort_order: str,
        filters: FilmFilter,
    ) -> list[Film]:
        sort_by = [
            {sort_field: {'order': sort_order}},
            {'_doc': {'order': 'asc'}},
        ]
        query = self._build_query(filters)
        search_params = {
            "index": MOVIES_INDEX,
            "query": query,
            "sort": sort_by,
            "from_": offset,
            "size": page_size,
        }
        try:
            docs = await self._elastic.search(**search_params)
        except ESNotFoundError as e:
            self._handle_not_found(e)

        films = []
        for doc in docs['hits']['hits']:
            try:
                film = Film(**doc['_source'])
                films.append(film)
            except (ValidationError, KeyError):
                film_id = doc.get('_id', 'unknown')
                logger.warning(
                    'Битые данные в ES для фильма %s, пропускаем',
                    film_id,
                    exc_info=True
                )
                continue
        return films

    def _build_query(self, filters: FilmFilter) -> dict:
        """Построение ES-запроса."""
        if not filters.has_any_filter():
            return {"match_all": {}}

        must_conditions = []
        filter_conditions = []

        text_filters = {
            'title': filters.title,
            'description': filters.description,
            'directors_names': filters.directors_names,
            'writers_names': filters.writers_names,
            'actors_names': filters.actors_names,
        }

        must_conditions = [
            {
                "match": {
                    field: {
                        'query': value,
                        'fuzziness': 'AUTO',
                        'operator': 'and',
                    }
                }
            }
            for field, value in text_filters.items()
            if value
        ]

        if filters.imdb_rating_from is not None or filters.imdb_rating_to is not None:
            range_condition = {}
            if filters.imdb_rating_from is not None:
                range_condition['gte'] = filters.imdb_rating_from
            if filters.imdb_rating_to is not None:
                range_condition['lte'] = filters.imdb_rating_to
            filter_conditions.append({"range": {'imdb_rating': range_condition}})

        query = {'bool': {}}
        if must_conditions:
            query['bool']['must'] = must_conditions
        if filter_conditions:
            query['bool']['filter'] = filter_conditions

        return query
