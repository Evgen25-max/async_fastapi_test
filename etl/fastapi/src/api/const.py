
from typing import Literal

MAX_OFFSET = 10000
SORTABLE_FIELDS = Literal['id', 'imdb_rating',]
SORT_ORDERS = Literal['asc', 'desc']
FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5


FILM_FIELDS_WHITELIST = {
    'id',
    'title',
    'description',
    'imdb_rating',
    'genres',
    'directors_names',
    'actors_names',
    'writers_names',
}
