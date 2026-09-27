
import functools
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from time import sleep

etl_logger = logging.getLogger('etl')


def movies_transform_elstic(all_data):
    movies_map = {}

    for row in all_data:
        fw_id = str(row['fw_id'])

        # Создаем базовую структуру для фильма
        if fw_id not in movies_map:
            movies_map[fw_id] = {
                "id": fw_id,
                "imdb_rating": float(row['rating']) if row['rating'] is not None else None,
                "genres": set(),
                "title": row['title'],
                "description": row['description'],
                "directors_names": set(),
                "actors_names": set(),
                "writers_names": set(),
                "directors": {},
                "actors": {},
                "writers": {},
            }

        movie = movies_map[fw_id]

        if row['genre_name']:
            movie["genres"].add(row['genre_name'])

        if row['person_id'] and row['full_name'] and row['role']:
            person = {"id": str(row['person_id']), "name": row['full_name']}
            role = row['role']

            if role == "director":
                movie["directors"][str(row['person_id'])] = person
                movie["directors_names"].add(row['full_name'])
            elif role == "actor":
                movie["actors"][str(row['person_id'])] = person
                movie["actors_names"].add(row['full_name'])
            elif role == "writer":
                movie["writers"][str(row['person_id'])] = person
                movie["writers_names"].add(row['full_name'])

    bulk_data = []
    for movie in movies_map.values():
        movie["genres"] = list(movie["genres"])
        movie["directors_names"] = list(movie["directors_names"])
        movie["actors_names"] = list(movie["actors_names"])
        movie["writers_names"] = list(movie["writers_names"])

        movie["directors"] = list(movie["directors"].values())
        movie["actors"] = list(movie["actors"].values())
        movie["writers"] = list(movie["writers"].values())

        bulk_data.append(movie)
    return bulk_data


def backoff(
    start_sleep_time=0.1,
    factor=2,
    border_sleep_time=10,
    max_tries=7,
    exceptions=(Exception,),
):
    """
    Декоратор для повторного выполнения функции.
    start_sleep_time: начальное время ожидания (сек)
    factor: во сколько раз увеличивать время ожидания на каждой итерации
    border_sleep_time: максимальное время ожидания (сек)
    max_tries: максимальное количество попыток
    exceptions: кортеж типов исключений, при которых нужно повторять
    :return: результат выполнения функции
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_tries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:

                    if attempt == max_tries - 1:
                        etl_logger.error(
                            f'Функция {func.__name__} исчерпала {max_tries} попыток. '
                            f'Последняя ошибка: {type(e).__name__}: {e}'
                            )
                        raise

                    # Рассчитываем время задержки по формуле
                    sleep_time = start_sleep_time * (factor ** attempt)
                    sleep_time = min(sleep_time, border_sleep_time)
                    etl_logger.error(
                        f'Ошибка в {func.__name__}: {type(e).__name__}. '
                        f'Попытка {attempt + 1}/{max_tries}. '
                        f'Следующая попытка через {sleep_time:.2f} сек...'
                        )
                    sleep(sleep_time)
                except Exception as e:
                    etl_logger.error(
                            f'Функция {func.__name__} вызвала нестандартную ошибку. '
                            f'Последняя ошибка: {type(e).__name__}: {e}'
                            )
                    raise e

        return wrapper
    return decorator


class SimpleLogger:
    def __init__(self, test=False, max_bytes=100*1024*1024, backup_count=5):
        self.logger = logging.getLogger('etl')
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            log_dir = 'log'
            os.makedirs(log_dir, exist_ok=True)

            prefix = 'test_' if test else ''
            log_filename = f'{prefix}{datetime.now():%Y-%m-%d}.log'
            log_path = os.path.join(log_dir, log_filename)

            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            self.logger.propagate = False

    def get_logger(self):
        return self.logger
