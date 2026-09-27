from typing import Optional

from core.config import config
from elasticsearch import AsyncElasticsearch

es: Optional[AsyncElasticsearch] = None


def init_elastic() -> None:
    """Инициализирует клиент."""
    global es
    es = AsyncElasticsearch(
        hosts=[f'{config.ELASTIC_SCHEMA}{config.ELASTIC_HOST}:{config.ELASTIC_PORT}'],
        sniff_on_connection_fail=True,
        retry_on_timeout=True,
        max_retries=config.ES_MAX_RETRIES,
        request_timeout=config.ES_REQUEST_TIMEOUT,
        connections_per_node=10,
        verify_certs=False,
    )


async def close_elastic() -> None:
    """Закрывает клиент."""
    global es
    if es is not None:
        await es.close()
        es = None


def get_elastic() -> AsyncElasticsearch:
    """Возвращает клиент."""
    if es is None:
        raise RuntimeError(
            'Elasticsearch не инициализирован. Вызовите init_elastic() при старте.'
        )
    return es
