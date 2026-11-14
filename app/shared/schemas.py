from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base de los contratos HTTP.

    Internamente usa ``snake_case`` (convención Python); en el JSON expone
    ``camelCase``, que es lo que espera el frontend Angular.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
