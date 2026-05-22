from pydantic import BaseModel, Field


class MLPredictionRequest(BaseModel):
    ticker: str = Field(default="PORTFOLIO", min_length=1, max_length=20)
    volatility: float = Field(..., gt=0)
    sharpe_ratio: float
    var_95: float
    beta: float
    market_return: float
    horizon_months: int = Field(default=12, ge=1, le=60)
    model_name: str = Field(default="gradient_boosting")


class MLPredictionResponse(BaseModel):
    predicted_return: float
    model_predictions: dict[str, float]
    horizon_months: int
    model_version: str
    model_type: str = "Ridge/Lasso/GradientBoostingRegressor"
    target: str = "Prediccion de retorno acumulado a horizonte fijo"
    interpretation: str


class MLAnomalyDetectionRequest(BaseModel):
    ticker: str = Field(default="PORTFOLIO", min_length=1, max_length=20)
    returns: list[float] = Field(..., min_length=20)
    contamination: float = Field(default=0.05, gt=0, lt=0.5)
    nu: float = Field(default=0.05, gt=0, lt=0.5)


class MLAnomalyPoint(BaseModel):
    index: int
    return_value: float
    isolation_forest_score: float
    one_class_svm_score: float
    is_anomaly_isolation_forest: bool
    is_anomaly_one_class_svm: bool
    is_anomaly_consensus: bool


class MLAnomalyDetectionResponse(BaseModel):
    ticker: str
    model_version: str
    model_type: str = "IsolationForest/OneClassSVM"
    target: str = "Deteccion de anomalias en retornos"
    observations: int
    anomalies_isolation_forest: int
    anomalies_one_class_svm: int
    anomalies_consensus: int
    points: list[MLAnomalyPoint]
    interpretation: str
