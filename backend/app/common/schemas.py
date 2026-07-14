"""Schemas compartilhados entre os módulos da API."""

from pydantic import BaseModel, ConfigDict


class StrictRequestModel(BaseModel):
    """Modelo-base que rejeita campos não declarados nos payloads da API."""

    model_config = ConfigDict(extra="forbid")
