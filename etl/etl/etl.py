import logging
from time import sleep

from elasticsearch.exceptions import ConnectionError, ConnectionTimeout
from psycopg2 import DatabaseError, InterfaceError, OperationalError

from const import TABLES, settings
from elastic_utils import ElasticBase
from pg_utils import PostgresBase
from state import State
from utils import movies_transform_elstic

etl_logger = logging.getLogger('etl')


class ETL:
    def __init__(
            self,
            pg: PostgresBase,
            transform: movies_transform_elstic,
            el: ElasticBase, state: State
            ):
        self.pg = pg
        self.transformer = transform
        self.el = el
        self.state = state

    def run(self, batch: int = 1000):
        etl_logger.info('Запуск ETL')
        self.el.add_index()
        state_etl = self.state.get_all_state()

        etl_logger.debug(
            f'Начальные значения state_last_val: {state_etl}'
            )
        while True:
            all_ids = set()
            try:
                etl_logger.debug(
                    f'Запрос id изм. фильмов.'
                    f'Limit по {batch} элементов'
                    )
                temp_state = state_etl.copy()
                for table in TABLES:
                    ids, temp_state = self.pg.get_changed_film_ids(
                                                temp_state,
                                                batch,
                                                table
                                                )
                    all_ids.update(ids)
                if not all_ids:
                    etl_logger.info('Новых изменений фильмов не найдено.')
                    sleep(settings.SLEEP_TIME*3)
                    continue
                etl_logger.debug(
                    'Запрос всех данных по измененным id фильмов.'
                    )
                all_films_data = self.pg.fetch_film_details(list(all_ids))
                transformed_data = self.transformer(all_films_data)
                etl_logger.debug(
                    f'Трансформировано {len(transformed_data)}'
                    'документов для ElasticSearch.'
                    )

                success, _ = self.el.bulk_load(transformed_data)

                if success > 0:
                    self.state.update_state(temp_state)
                    state_etl.update(temp_state)
                    etl_logger.debug(
                        f'Состояние успешно сохранено.'
                        f'Новая состояния: {state_etl}'
                        )
                else:
                    etl_logger.error(
                        'Ошибка загрузки в Elastic.'
                        ' Состояние не обновлено,'
                        ' данные будут обработаны повторно.'
                        )
                    sleep(settings.SLEEP_TIME)
                    continue

            except (OperationalError, InterfaceError, DatabaseError) as e:
                etl_logger.error(
                        f'Ошибка работы с БД postgres. '
                        f'Перезапуск через: {settings.SLEEP_TIME}'
                        f'{type(e).__name__}: {e}'
                        )
                sleep(settings.SLEEP_TIME)
                continue
            except (ConnectionError, ConnectionTimeout) as e:
                etl_logger.error(
                    f'Ошибка работы с ElasticSearch. '
                    f'Перезапуск через: {settings.SLEEP_TIME}'
                    f'{type(e).__name__}: {e}'
                        )
                sleep(settings.SLEEP_TIME)
                continue
            except Exception as e:
                etl_logger.exception(
                    f'Ошибка работы. Нестандартная ошибка.'
                    f'{type(e).__name__}: {e}')
                sleep(settings.SLEEP_TIME)
