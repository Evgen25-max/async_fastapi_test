import uuid

import pytest
from settings import test_settings

BASE_URL = test_settings.service_url


def get_items(data):
    """Выдача фильмов из ответа API."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get('results', data.get('items', data.get('films', [])))
    return []


def generate_films(count: int, base_title: str = 'Test Movie'):
    """Генератор фильмов."""
    films = []
    for i in range(count):
        films.append({
            'id': str(uuid.uuid4()),
            'imdb_rating': round(float((i % 10) + 0.5), 1),
            'genres': ['Action', 'Drama'],
            'title': f'{base_title} {i}',
            'description': f'Description for {i}',
            'directors_names': ['Director Name'],
            'actors_names': ['Actor Name'],
            'writers_names': ['Writer Name'],
            'directors': [{'id': str(uuid.uuid4()), 'name': 'Director Name'}],
            'actors': [{'id': str(uuid.uuid4()), 'name': 'Actor Name'}],
            'writers': [{'id': str(uuid.uuid4()), 'name': 'Writer Name'}],
        })
    return films


@pytest.mark.asyncio
async def test_film_details_success(aiohttp_client, clean_es, clean_redis, load_films):
    films = generate_films(1, 'Unique Detail Movie')
    await load_films(films)

    url = f'{BASE_URL}/api/v1/films/{films[0]['id']}'
    async with aiohttp_client.get(url) as response:
        assert response.status == 200
        data = await response.json()
        assert data['id'] == films[0]['id']
        assert data['title'] == films[0]['title']


@pytest.mark.asyncio
async def test_film_details_not_found(aiohttp_client, clean_es, clean_redis):
    random_id = str(uuid.uuid4())
    url = f'{BASE_URL}/api/v1/films/{random_id}'
    async with aiohttp_client.get(url) as response:
        assert response.status == 404


@pytest.mark.asyncio
async def test_film_details_invalid_uuid(aiohttp_client, clean_es, clean_redis):
    """Некорректный UUID."""
    url = f'{BASE_URL}/api/v1/films/not-a-valid-uuid'
    async with aiohttp_client.get(url) as response:
        assert response.status in (404, 422)


@pytest.mark.asyncio
async def test_film_details_redis_cache(aiohttp_client, clean_es, clean_redis, load_films, es_client):
    films = generate_films(1, 'Cache Detail Movie')
    await load_films(films)
    film_id = films[0]['id']
    url = f'{BASE_URL}/api/v1/films/{film_id}'

    async with aiohttp_client.get(url) as response:
        assert response.status == 200
        data1 = await response.json()

    await es_client.indices.delete(index='movies')

    async with aiohttp_client.get(url) as response:
        assert response.status == 200
        data2 = await response.json()
        assert data1['id'] == data2['id']


@pytest.mark.asyncio
async def test_all_films_pagination(aiohttp_client, clean_es, clean_redis, load_films):
    films = generate_films(15, 'Pagination Movie')
    await load_films(films)

    url = f'{BASE_URL}/api/v1/films/'
    async with aiohttp_client.get(url) as response:
        assert response.status == 200
        data = await response.json()
        items = get_items(data)
        assert len(items) > 0


@pytest.mark.asyncio
async def test_all_films_limit_n_records(aiohttp_client, clean_es, clean_redis, load_films):
    films = generate_films(25, 'Limit Movie')
    await load_films(films)

    url = f'{BASE_URL}/api/v1/films/?page=1&page_size=5'
    async with aiohttp_client.get(url) as response:
        assert response.status == 200
        data = await response.json()
        items = get_items(data)
        assert len(items) == 5


@pytest.mark.asyncio
async def test_all_films_search_by_phrase(aiohttp_client, clean_es, clean_redis, load_films):
    """Поиск записей по фразе (параметр title)."""
    films = generate_films(2, 'KuKu Movie')
    films.extend(generate_films(2, 'LuLu Movie'))

    await load_films(films)

    url = f'{BASE_URL}/api/v1/films/?title=KuKu'
    async with aiohttp_client.get(url) as response:
        assert response.status == 200
        data = await response.json()
        items = get_items(data)
        assert len(items) >= 1
        assert any('KuKu' in item['title'] for item in items)


@pytest.mark.asyncio
async def test_all_films_redis_cache(aiohttp_client, clean_es, clean_redis, load_films, es_client):
    films = generate_films(5, 'Cache Movie')
    await load_films(films)

    url = f'{BASE_URL}/api/v1/films/?title=Cache'

    async with aiohttp_client.get(url) as response:
        assert response.status == 200
        data1 = await response.json()
        items1 = get_items(data1)
        assert len(items1) == 5

    await es_client.indices.delete(index='movies')

    async with aiohttp_client.get(url) as response:
        assert response.status == 200
        data2 = await response.json()
        items2 = get_items(data2)
        assert len(items2) == 5
        assert items1 == items2


@pytest.mark.asyncio
async def test_all_films_invalid_page(aiohttp_client, clean_es, clean_redis):
    """Некорректный номер страницы (page < 1)."""
    url = f'{BASE_URL}/api/v1/films/?page=0'
    async with aiohttp_client.get(url) as response:
        assert response.status == 422


@pytest.mark.asyncio
async def test_all_films_invalid_page_size(aiohttp_client, clean_es, clean_redis):
    """Некорректный размер страницы (page_size > 100 или < 1)."""
    url = f'{BASE_URL}/api/v1/films/?page_size=101'
    async with aiohttp_client.get(url) as response:
        assert response.status == 422

    url2 = f'{BASE_URL}/api/v1/films/?page_size=0'
    async with aiohttp_client.get(url2) as response:
        assert response.status == 422


@pytest.mark.asyncio
async def test_all_films_invalid_sort(aiohttp_client, clean_es, clean_redis):
    """Cортировка по несуществующему полю."""
    url = f'{BASE_URL}/api/v1/films/?sort=invalid_field'
    async with aiohttp_client.get(url) as response:
        assert response.status in (422, 200)
