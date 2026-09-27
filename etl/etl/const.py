
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = '127.0.0.1'
    SQL_PORT: int = 5432

    ELASTIC_HOST: str = '127.0.0.1'
    ELASTIC_PORT: int = 9200

    BATCH_SIZE: int = 1000
    SLEEP_TIME: int = 60
    FILE_STATE: str = 'state/state.txt'
    INDEX_NAME: str = 'movies'

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra="ignore",
    )

    @property
    def pg_connection_conf(self) -> str:
        return (
            f'dbname={self.POSTGRES_DB} '
            f'user={self.POSTGRES_USER} '
            f'password={self.POSTGRES_PASSWORD} '
            f'host={self.POSTGRES_HOST} '
            f'port={self.SQL_PORT}'
        )

    @property
    def elasticsearch_url(self) -> str:
        return f'http://{self.ELASTIC_HOST}:{self.ELASTIC_PORT}'


settings = Settings()

INDEX_CONFIG = {
    "settings": {
        "refresh_interval": "1s",
        "analysis": {
            "filter": {
                "english_stop": {"type": "stop", "stopwords": "_english_"},
                "english_stemmer": {"type": "stemmer", "language": "english"},
                "english_possessive_stemmer": {"type": "stemmer", "language": "possessive_english"},
                "russian_stop": {"type": "stop", "stopwords": "_russian_"},
                "russian_stemmer": {"type": "stemmer", "language": "russian"}
            },
            "analyzer": {
                "ru_en": {
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "english_stop",
                        "english_stemmer",
                        "english_possessive_stemmer",
                        "russian_stop",
                        "russian_stemmer"
                    ]
                }
            }
        }
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "id": {"type": "keyword"},
            "imdb_rating": {"type": "float"},
            "genres": {"type": "keyword"},
            "title": {
                "type": "text",
                "analyzer": "ru_en",
                "fields": {"raw": {"type": "keyword"}}
            },
            "description": {"type": "text", "analyzer": "ru_en"},
            "directors_names": {"type": "text", "analyzer": "ru_en"},
            "actors_names": {"type": "text", "analyzer": "ru_en"},
            "writers_names": {"type": "text", "analyzer": "ru_en"},
            "directors": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "ru_en"}
                }
            },
            "actors": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "ru_en"}
                }
            },
            "writers": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "ru_en"}
                }
            }
        }
    }
}


SELECT_ID_MODIFIED = """
    SELECT content.{table_name}.id, content.{table_name}.{col_name}, content.film_work.id as fw_id
    FROM content.film_work
    {inner}
    WHERE (content.{table_name}.{col_name}, content.{table_name}.id) > (%(mod)s, %(id_val)s)
    {add_where}
    ORDER BY content.{table_name}.{col_name}, content.{table_name}.id
    LIMIT %(batch)s;
"""


GET_MODIFY_CREATED = {
    'film_work': 'modified',
    'person': 'modified',
    'genre': 'modified',
    'person_film_work': 'created',
    'genre_film_work': 'created'
}

TABLES = [
    'film_work', 'person', 'genre', 'person_film_work', 'genre_film_work'
    ]

QUERY_TABLE = {
    'film_work': {'inner': '',
                  'add_where': ''},
    'person': {'inner': """INNER JOIN content.person_film_work ON content.person_film_work.film_work_id=content.film_work.id
                INNER JOIN content.person ON content.person_film_work.person_id=content.person.id""",
               'add_where': 'and content.person.modified > content.film_work.modified'},
    'genre': {'inner': """INNER JOIN content.genre_film_work ON content.genre_film_work.film_work_id=content.film_work.id
                INNER JOIN content.genre ON content.genre_film_work.genre_id=content.genre.id""",
              'add_where': 'and content.genre.modified > content.film_work.modified'},
    'person_film_work': {'inner': """INNER JOIN content.person_film_work ON content.person_film_work.film_work_id=content.film_work.id""",
                         'add_where': 'and content.person_film_work.created > content.film_work.modified'},
    'genre_film_work': {'inner': """INNER JOIN content.genre_film_work ON content.genre_film_work.film_work_id=content.film_work.id""",
                        'add_where': 'and content.genre_film_work.created > content.film_work.modified'},
}
