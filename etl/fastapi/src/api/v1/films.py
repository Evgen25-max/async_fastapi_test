from http import HTTPStatus

from api.const import MAX_OFFSET, SORT_ORDERS, SORTABLE_FIELDS
from api.filters import FilmFilter
from api.utils import get_include_fields
from elasticsearch import NotFoundError
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from services.film import FilmService, get_film_service

router = APIRouter()


@router.get('/{film_id}')
async def film_details(
    film_id: str,
    film_service: FilmService = Depends(get_film_service)
) -> JSONResponse:
    try:
        film = await film_service.get_by_id(film_id)
    except NotFoundError:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Film {film_id} not found',
        )

    return JSONResponse(content=film.model_dump())


@router.get('/')
async def all_films(
    page: int = Query(1, ge=1, description='Номер страницы'),
    page_size: int = Query(20, ge=1, le=100, description='Фильмов на странице'),
    sort: SORTABLE_FIELDS = Query("id", description='Поле для сортировки'),
    order: SORT_ORDERS = Query("asc", description="Направление сортировки"),
    title: str | None = Query(None, min_length=1, max_length=255, description='Поиск по названию фильма'),
    description: str | None = Query(None, min_length=1, max_length=255, description='Поиск по описанию фильма'),
    directors_names: str | None = Query(None, min_length=1, max_length=100, description='Поиск по именам режиссёров'),
    writers_names: str | None = Query(None, min_length=1, max_length=100, description='Поиск по именам сценаристов'),
    actors_names: str | None = Query(None, min_length=1, max_length=100, description='Поиск по именам актёров'),
    imdb_rating_from: float | None = Query(None, ge=0.0, le=10.0, description='Рейтинг imdb >='),
    imdb_rating_to: float | None = Query(None, ge=0.0, le=10.0, description='Рейтинг imdb <='),
    include_fields: set[str] = Depends(get_include_fields),
    film_service: FilmService = Depends(get_film_service),
) -> JSONResponse:
    try:
        filters = FilmFilter(
            title=title,
            description=description,
            directors_names=directors_names,
            writers_names=writers_names,
            actors_names=actors_names,
            imdb_rating_from=imdb_rating_from,
            imdb_rating_to=imdb_rating_to,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    offset = (page - 1) * page_size
    if offset + page_size > MAX_OFFSET:
        raise HTTPException(
            status_code=400,
            detail='Слишком глубокая страница. '
                   'Используйте фильтры для уточнения запроса.'
        )
    sort_by = [
        {sort: {'order': order}},
        {'_doc': {'order': 'asc'}},
        ]
    films = await film_service.get_all(
        offset=offset,
        page_size=page_size,
        sort_by=sort_by,
        filters=filters,
        include_fields=include_fields,
        )
    result = [film.model_dump(include=include_fields) for film in films]

    return JSONResponse(content=result)
