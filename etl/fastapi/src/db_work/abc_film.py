from abc import ABC, abstractmethod
from typing import Optional

from api.filters import FilmFilter
from models.film import Film


class FilmRepository(ABC):
    """Абстракция хранилища фильмов."""

    @abstractmethod
    async def get_by_id(self, film_id: str) -> Optional[Film]:
        ...

    @abstractmethod
    async def get_all(
        self,
        offset: int,
        page_size: int,
        sort_field: str,
        sort_order: str,
        filters: FilmFilter,
    ) -> list[Film]:
        ...
