
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import OperationalError, InterfaceError, DatabaseError
from typing import List, Dict
from utils import backoff
import logging
from typing import List, Dict, Tuple
from const import SELECT_ID_MODIFIED, GET_MODIFY_CREATED, QUERY_TABLE
from psycopg2 import sql


etl_logger = logging.getLogger('etl')


class PostgresBase:
    def __init__(self, conf: str):
        self.conf = conf

    def _get_connection(self):
        try:
            return psycopg2.connect(self.conf)
        except psycopg2.OperationalError as e:
            etl_logger.critical(f"Ошибка подключения к PostgreSQL: {e}")
            raise e

    @backoff(exceptions=(OperationalError, InterfaceError, DatabaseError))
    def get_changed_film_ids(self, state: Dict, batch: int, table: str) -> Tuple[List[str], str, str]:
        film_ids = []
        new_state = state.copy()
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                try:
                    query = sql.SQL(SELECT_ID_MODIFIED).format(
                                col_name=sql.Identifier(GET_MODIFY_CREATED[table]),
                                table_name=sql.Identifier(table),
                                inner=sql.SQL(QUERY_TABLE[table]['inner']),
                                add_where=sql.SQL(QUERY_TABLE[table]['add_where'])
                                )
                    cursor.execute(
                            query,
                            {
                                'mod': state[f'{table}_modified'],
                                'id_val': state[f'{table}_id'],
                                'batch': batch
                            }
                            )
                except Exception as e:
                    raise e
                instances = cursor.fetchall()
                if instances:
                    new_state[f'{table}_modified'] = instances[-1][GET_MODIFY_CREATED[table]].isoformat()
                    new_state[f'{table}_id'] = str(instances[-1]['id'])
                film_ids = [row['fw_id'] for row in instances]
        return film_ids, new_state

    @backoff(
        exceptions=(OperationalError, InterfaceError, DatabaseError)
    )
    def fetch_film_details(self, film_ids: List[str]) -> List[Dict]:
        if not film_ids:
            return []
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT
                        fw.id          AS fw_id,
                        fw.title       AS title,
                        fw.description AS description,
                        fw.rating      AS rating,
                        pfw.role       AS role,
                        p.id           AS person_id,
                        p.full_name    AS full_name,
                        g.name         AS genre_name
                    FROM content.film_work fw
                    LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
                    LEFT JOIN content.person p ON p.id = pfw.person_id
                    LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
                    LEFT JOIN content.genre g ON g.id = gfw.genre_id
                    WHERE fw.id = ANY(%s::uuid[]);
                    """,
                    (film_ids,)
                )
                return cursor.fetchall()
