
class FilmNotFoundError(Exception):
    def __init__(self, film_id: str):
        self.film_id = film_id
