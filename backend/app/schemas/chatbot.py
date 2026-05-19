from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ChatbotQuestionRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Pregunta del usuario sobre teoría del riesgo o métricas del proyecto",
    )
    mode: str = Field(
        default="general",
        description="Modo de respuesta: general o estadistico",
    )
    module: str | None = Field(
        default=None,
        max_length=80,
        description="Módulo opcional asociado a la pregunta: var, capm, garch, markowitz, perri, etc.",
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("La pregunta no puede estar vacía")
        return cleaned

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"general", "estadistico"}:
            raise ValueError("mode debe ser 'general' o 'estadistico'")
        return cleaned

    @field_validator("module")
    @classmethod
    def validate_module(cls, value: str | None) -> str | None:
        if value is None:
            return value

        cleaned = value.strip().lower()
        return cleaned or None


class ChatbotSourceItem(BaseModel):
    title: str = Field(..., description="Nombre de la fuente usada")
    source_type: str = Field(..., description="Tipo de fuente: teoria, modulo, metodologia o sistema")
    reference: str = Field(..., description="Referencia textual corta de la fuente")


class ChatbotAnswerResponse(BaseModel):
    question: str = Field(..., description="Pregunta normalizada del usuario")
    mode: str = Field(..., description="Modo usado para responder")
    module: str | None = Field(default=None, description="Módulo detectado o enviado")
    supported: bool = Field(..., description="Indica si la pregunta está soportada por la base de conocimiento local")
    answer: str = Field(..., description="Respuesta del chatbot experto")
    topics: list[str] = Field(default_factory=list, description="Temas detectados")
    sources: list[ChatbotSourceItem] = Field(default_factory=list, description="Fuentes internas usadas")
    suggested_followups: list[str] = Field(
        default_factory=list,
        description="Preguntas sugeridas para continuar",
    )
