from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import PredictionLog
from app.ml.predictor import MLPredictor
from app.schemas.ml_schema import MLAnomalyDetectionRequest, MLAnomalyDetectionResponse


router = APIRouter(tags=["Machine Learning"])


def get_predictor() -> MLPredictor:
    return MLPredictor()


@router.get("/status")
def get_ml_status(predictor: MLPredictor = Depends(get_predictor)) -> dict:
    return predictor.metadata()


@router.post("/predict", response_model=MLAnomalyDetectionResponse)
def predict_anomalies(
    payload: MLAnomalyDetectionRequest,
    predictor: MLPredictor = Depends(get_predictor),
    db: Session = Depends(get_db),
):
    try:
        result = predictor.predict(returns=payload.returns, ticker=payload.ticker)
        db.add(
            PredictionLog(
                model_version=predictor.model_version,
                ticker=payload.ticker.strip().upper() or "PORTFOLIO",
                input_features={
                    "returns_count": len(payload.returns),
                    "contamination": payload.contamination,
                    "nu": payload.nu,
                    "task": "anomaly_detection",
                },
                prediction=float(result["anomalies_consensus"]),
            )
        )
        db.commit()
        return MLAnomalyDetectionResponse(**result)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
