# Endpoints backend disponibles para frontend

## Machine Learning

GET /api/v1/ml/status

POST /api/v1/ml/predict

Payload:
{
  "volatility": 0.22,
  "sharpe_ratio": 1.15,
  "var_95": -0.08,
  "beta": 1.10,
  "market_return": 0.12
}

## Renta fija

POST /api/v1/valuation/nelson-siegel

Payload:
{
  "yields": [0.03, 0.035, 0.04, 0.045],
  "maturities": [1, 2, 5, 10]
}

Uso frontend:
- Grafica curva observada vs curva ajustada.
- KPI beta0, beta1, beta2, tau y RMSE.

## Opciones

POST /api/v1/valuation/black-scholes

Payload:
{
  "spot_price": 100,
  "strike_price": 105,
  "time_to_maturity": 1,
  "risk_free_rate": 0.05,
  "volatility": 0.2,
  "option_type": "call"
}

Uso frontend:
- KPI precio teorico.
- KPI delta, gamma y vega.
- Sensibilidad por volatilidad.

## Stress testing

POST /api/v1/stress/scenario

Payload:
{
  "portfolio_value": 100000,
  "expected_return": 0.12,
  "volatility": 0.20,
  "var_95": -0.08,
  "beta": 1.15,
  "rate_shock": 0.03,
  "market_shock": -0.15,
  "volatility_multiplier": 1.5
}

Uso frontend:
- KPI perdida estimada.
- KPI valor estresado.
- Semaforo de severidad.
- Grafica antes/despues.
- Interpretacion ejecutiva.

## Validacion backend actual

- python -m compileall backend\app
- python -m pytest tests -v
- Resultado validado: 53 passed
- Docker backend validado en puerto 8001
