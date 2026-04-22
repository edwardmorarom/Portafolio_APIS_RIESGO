from pydantic import BaseModel, Field


class DecisionRouterResponse(BaseModel):
    message: str = Field(..., description="Mensaje del módulo de decisión")