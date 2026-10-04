import aiohttp
import pytest_asyncio
import redis.asyncio as redis
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from settings import test_settings

ES_URL = f'{test_settings.ELASTIC_SCHEMA}{test_settings.ELASTIC_HOST}:{test_settings.ELASTIC_PORT}'
INDEX_NAME = test_settings.es_index


@pytest_asyncio.fixture(scope='function')
async def aiohttp_client():
    async with aiohttp.ClientSession() as session:
        yield session


@pytest_asyncio.fixture(scope='function')
async def es_client():
    client = AsyncElasticsearch(hosts=[ES_URL])
    yield client
    await client.close()


@pytest_asyncio.fixture(scope='function')
async def clean_es(es_client: AsyncElasticsearch):
    """Удаляет и пересоздаёт индекс с маппингом из settings."""
    if await es_client.indices.exists(index=INDEX_NAME):
        await es_client.indices.delete(index=INDEX_NAME)

    await es_client.indices.create(index=INDEX_NAME, **test_settings.es_index_mapping)

    yield es_client


@pytest_asyncio.fixture(scope='function')
async def clean_redis():
    client = redis.Redis(
        host=test_settings.REDIS_HOST,
        port=test_settings.REDIS_PORT,
        password=test_settings.REDIS_PASSW,
        decode_responses=True,
    )
    await client.flushdb()
    yield client
    await client.aclose()


@pytest_asyncio.fixture(scope='function')
async def load_films(es_client: AsyncElasticsearch):
    async def _load_films(films_data: list):
        bulk_query = [
            {'_index': INDEX_NAME, '_id': row['id'], '_source': row}
            for row in films_data
        ]
        updated, errors = await async_bulk(client=es_client, actions=bulk_query)
        if errors:
            raise Exception(f'Ошибка записи данных в Elasticsearch: {errors}')
        await es_client.indices.refresh(index=INDEX_NAME)
    return _load_films
