from abc import ABC, abstractmethod
from typing import Optional

from models.film import Film


class FilmCache(ABC):
    """Абстракция кэша фильмов."""

    @abstractmethod
    async def get_film(self, film_id: str) -> Optional[Film]:
        ...

    @abstractmethod
    async def put_film(self, film: Film) -> None:
        ...

    @abstractmethod
    async def get_films_list(self, cache_key: str) -> Optional[list[Film]]:
        ...

    @abstractmethod
    async def put_films_list(self, cache_key: str, films: list[Film]) -> None:
        ...
