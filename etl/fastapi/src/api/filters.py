from pydantic import BaseModel, Field, model_validator


class FilmFilter(BaseModel):
    title: str | None = None
    description: str | None = None
    directors_names: str | None = None
    writers_names: str | None = None
    actors_names: str | None = None
    imdb_rating_from: float | None = Field(None, ge=0.0, le=10.0)
    imdb_rating_to: float | None = Field(None, ge=0.0, le=10.0)

    @model_validator(mode="after")
    def check_rating_range(self):
        if (
            self.imdb_rating_from is not None
            and self.imdb_rating_to is not None
            and self.imdb_rating_from > self.imdb_rating_to
        ):
            raise ValueError(
                'imdb_rating_from не может быть больше imdb_rating_to'
                )
        return self

    def has_any_filter(self) -> bool:
        return any(
            value is not None
            for value in [
                self.title,
                self.directors_names,
                self.writers_names,
                self.actors_names,
                self.description,
                self.imdb_rating_from,
                self.imdb_rating_to,
            ]
        )
