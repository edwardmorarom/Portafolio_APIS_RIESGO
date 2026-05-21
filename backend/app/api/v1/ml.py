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
            horizon_months=payload.horizon_months,
            model_name=payload.model_name,
        )
        model_predictions = predictor.predict_all(
            volatility=payload.volatility,
            sharpe_ratio=payload.sharpe_ratio,
            var_95=payload.var_95,
            beta=payload.beta,
            market_return=payload.market_return,
            horizon_months=payload.horizon_months,
        )

        if prediction >= 0.10:
            interpretation = "Predicción favorable: el retorno acumulado estimado compensa mejor el riesgo ingresado."
        elif prediction >= 0.00:
            interpretation = "Predicción moderada: el retorno acumulado estimado es positivo, pero requiere contrastar con VaR y volatilidad."
        else:
            interpretation = "Predicción adversa: el retorno acumulado estimado es bajo o negativo y debe leerse como alerta de riesgo."

        return MLPredictionResponse(
            predicted_return=prediction,
            model_predictions=model_predictions,
            horizon_months=payload.horizon_months,
            model_version=MODEL_VERSION,
            model_type=MODEL_TYPE,
            target=MODEL_TARGET,
            interpretation=interpretation,
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
