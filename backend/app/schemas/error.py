from pydantic import BaseModel, Field
from typing import Any


class ErrorDetail(BaseModel):
    error_code: str = Field(..., description="Codigo interno del error")
    message: str = Field(..., description="Mensaje principal")
    hint: str | None = Field(default=None, description="Sugerencia para corregir el error")
    where: str | None = Field(default=None, description="Modulo o componente donde ocurre")
    extra: dict[str, Any] = Field(default_factory=dict, description="Contexto adicional")


class ErrorResponse(BaseModel):
    detail: ErrorDetail