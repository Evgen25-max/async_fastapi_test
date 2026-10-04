
from const import INDEX_CONFIG, settings
from elastic_utils import ElasticBase
from etl import ETL
from pg_utils import PostgresBase
from state import JsonFileStorage, State
from utils import SimpleLogger, movies_transform_elstic

if __name__ == '__main__':
    logger_setup = SimpleLogger()
    logger = logger_setup.get_logger()

    storage = JsonFileStorage(settings.FILE_STATE)
    try:
        state = State(storage)
    except Exception as e:
        logger.critical(
            'Не найден файл состояния. Аварийное выключение.'
            f'{type(e).__name__}: {e}'
            )
        raise e
    pg_base = PostgresBase(settings.pg_connection_conf)

    try:
        el_base = ElasticBase(settings.elasticsearch_url, settings.INDEX_NAME, INDEX_CONFIG)
    except Exception as e:
        logger.critical(
            'Нет подключения к БД Elasticsearch. Аварийное выключение.'
            f'{type(e).__name__}: {e}'
            )
        raise e
    etl = ETL(pg_base, movies_transform_elstic, el_base, state)
    etl.run(batch=settings.BATCH_SIZE)
