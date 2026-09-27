
# Используем pydantic для упрощения работы при перегонке данных из json в объекты
from typing import Optional

from pydantic import BaseModel


class Film(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    imdb_rating: Optional[float] = None
    genres: list[str] = []
    directors_names: list[str] = []
    actors_names: list[str] = []
    writers_names: list[str] = []
