from fastapi import APIRouter, HTTPException

from app.ml.predictor import MODEL_TARGET, MODEL_TYPE, MODEL_VERSION, MLPredictor
from app.schemas.ml_schema import MLPredictionRequest, MLPredictionResponse


router = APIRouter(tags=["Machine Learning"])

predictor = MLPredictor()


@router.get("/status")
def get_ml_status() -> dict:
    return predictor.metadata()


@router.post("/predict", response_model=MLPredictionResponse)
def predict_return(payload: MLPredictionRequest):
    try:
        prediction = predictor.predict(
            volatility=payload.volatility,
            sharpe_ratio=payload.sharpe_ratio,
            var_95=payload.var_95,
            beta=payload.beta,
            market_return=payload.market_return,
        )

        if prediction >= 0.10:
            interpretation = "Predicción favorable: el retorno esperado compensa mejor el riesgo ingresado."
        elif prediction >= 0.00:
            interpretation = "Predicción moderada: el retorno esperado es positivo, pero requiere contrastar con VaR y volatilidad."
        else:
            interpretation = "Predicción adversa: el retorno esperado es bajo o negativo y debe leerse como alerta de riesgo."

        return MLPredictionResponse(
            predicted_return=prediction,
            model_version=MODEL_VERSION,
            model_type=MODEL_TYPE,
            target=MODEL_TARGET,
            interpretation=interpretation,
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
