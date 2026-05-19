from fastapi import APIRouter

from app.core.settings import get_settings
from app.ml.predictor import MODEL_VERSION, MLPredictor


router = APIRouter()


@router.get("/status")
def get_system_status() -> dict:
    settings = get_settings()

    predictor = MLPredictor()

    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "environment": settings.app_env,
        "debug": settings.debug,
        "api_prefix": settings.api_v1_prefix,
        "database_configured": bool(settings.database_url),
        "ml_enabled": predictor.is_loaded(),
        "ml_model_version": MODEL_VERSION,
        "chatbot_provider": settings.llm_provider,
        "chatbot_model": settings.llm_model,
    }
