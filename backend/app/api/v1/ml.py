from fastapi import APIRouter, HTTPException

from app.ml.predictor import MLPredictor
from app.schemas.ml_schema import (
    MLPredictionRequest,
    MLPredictionResponse,
)

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

predictor = MLPredictor()


@router.post(
    "/predict",
    response_model=MLPredictionResponse,
)
def predict_return(payload: MLPredictionRequest):
    try:
        prediction = predictor.predict(
            volatility=payload.volatility,
            sharpe_ratio=payload.sharpe_ratio,
            var_95=payload.var_95,
            beta=payload.beta,
            market_return=payload.market_return,
        )

        return MLPredictionResponse(
            predicted_return=prediction,
            model_version="1.0.0",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )
