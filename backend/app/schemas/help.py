from pydantic import BaseModel, Field


class HelpItem(BaseModel):
    key: str = Field(...)
    general: str = Field(...)
    estadistico: str = Field(...)


class HelpCatalogResponse(BaseModel):
    total_items: int = Field(...)
    items: list[HelpItem] = Field(default_factory=list)