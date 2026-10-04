from typing import Annotated

from fastapi import Query

from api.const import FILM_FIELDS_WHITELIST

FieldsParam = Annotated[
    str | None,
    Query(
        description='Список полей через запятую, например: id,title.\n'
        f'Cписок доступных полей: {', '.join(sorted(FILM_FIELDS_WHITELIST))}'
        )
]
