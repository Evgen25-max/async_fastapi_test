
class FilmNotFoundError(Exception):
    def __init__(self, film_id: str):
        self.film_id = film_id


class FilmDataError(Exception):
    """Документ существует, но данные повреждены."""
    def __init__(self, film_id: str):
        self.film_id = film_id
        super().__init__(f'Данные фильмы повреждены id: {film_id}')


class IndexNotFoundError(Exception):
    """Индекс в хранилище отсутствует или недоступен."""
    def __init__(self, index_name: str):
        self.index_name = index_name
        super().__init__(f'Index {index_name} not found')
