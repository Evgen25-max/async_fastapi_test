
from fastapi import HTTPException, status

from api.const import FILM_FIELDS_WHITELIST
from api.params import FieldsParam


async def get_include_fields(
    fields: FieldsParam = None,
) -> set[str]:
    """
    Парсит параметр fields из query.
    """
    if not fields:
        return set(FILM_FIELDS_WHITELIST)

    requested_fields = {
        field.strip()
        for field in fields.split(",")
        if field.strip()
    }

    invalid_fields = requested_fields - FILM_FIELDS_WHITELIST

    if invalid_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Invalid fields: {', '.join(invalid_fields)}',
        )
    requested_fields.add('id')

    return requested_fields
