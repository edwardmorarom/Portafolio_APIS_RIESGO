# Guion de Sustentacion - Proyecto Integrador Riesgo Python CIII

Fecha de revision: 2026-05-22

Este guion ayuda a defender el proyecto en vivo. No reemplaza la demo: sirve para ordenar la explicacion y evitar respuestas vagas.

## 1. Apertura

Objetivo del sistema:

- Analizar un portafolio de minimo cinco activos desde riesgo, rendimiento, optimizacion, renta fija, derivados, stress testing y ML.
- Separar calculo financiero en backend FastAPI y visualizacion en Streamlit.
- Usar persistencia SQLite/SQLAlchemy para precios, activos, portafolios guardados y logs de prediccion.

Mensaje corto:

> Construimos una plataforma modular de analisis de riesgo. El frontend consume el backend, el backend valida con Pydantic, calcula con servicios financieros y persiste datos con SQLAlchemy.

## 2. Ruta de demo sugerida

1. Contextualizacion:
   - Mostrar portafolio activo, universo de activos, benchmark y estado del backend.

2. Rendimientos e indicadores tecnicos:
   - Mostrar que los datos vienen del backend.
   - Explicar rendimiento simple vs logaritmico.
   - Mostrar indicadores tecnicos como senales, no como prediccion perfecta.

3. GARCH / EWMA:
   - Mostrar EWMA, volatilidad rodante, ARCH/GARCH/EGARCH, AIC/BIC y forecast multi-paso.
   - Defender que EWMA reacciona por decaimiento exponencial y GARCH modela volatilidad condicional.
   - Revisar Jarque-Bera y ARCH-LM.

4. VaR / CVaR:
   - Mostrar VaR historico, parametrico y Monte Carlo.
   - Explicar Kupiec como backtesting de excepciones.

5. CAPM y benchmark:
   - Mostrar beta, alpha de Jensen, R2 y benchmark seleccionado.
   - Explicar que beta mide sensibilidad frente al mercado.

6. Markowitz:
   - Mostrar frontera eficiente, minima varianza, maximo Sharpe y comparacion con/sin short selling.
   - Explicar restriccion long-only: pesos no negativos y suma 100%.
   - Explicar version con short selling como comparacion metodologica, no recomendacion operativa.

7. Renta fija:
   - Mostrar curva Treasury/FRED o fallback marcado.
   - Mostrar Nelson-Siegel, RMSE, duracion, duracion modificada, convexidad y sensibilidad +/-50, +/-100, +/-200 pb.
   - Defender la diferencia entre aproximacion lineal, duracion + convexidad y repricing exacto.

8. Opciones:
   - Mostrar Black-Scholes para call/put y cinco Greeks.
   - Explicar que las Greeks son sensibilidades: delta, gamma, vega, theta y rho.

9. Stress testing:
   - Mostrar shocks de mercado, tasa y volatilidad.
   - Explicar que no es pronostico: es una prueba de resiliencia.

10. Machine Learning:
    - Mostrar status del modelo, Singleton y endpoint `/api/v1/ml/predict`.
    - Explicar que la prediccion queda registrada en `PredictionLog`.

11. Reporte:
    - Generar o mostrar reporte ejecutivo PDF.
    - Aclarar que las metricas no calculadas se marcan como N/D.

## 3. Defensa tecnica

FastAPI:

- Routers en `backend/app/api/v1`.
- Schemas Pydantic en `backend/app/schemas`.
- Servicios financieros en `backend/app/services`.
- Clientes externos en `backend/app/clients`.
- Dependencias con `Depends` en `backend/app/core/dependencies.py`.

SQLAlchemy:

- `Asset`: universo de activos.
- `Price`: cache historica de precios.
- `Portfolio`: portafolios guardados.
- `PredictionLog`: trazabilidad de predicciones ML.

ML:

- Predictor Singleton evita cargar el modelo en cada request.
- Modelo persistido con `joblib`.
- Endpoint `/api/v1/ml/status` muestra estado y `/api/v1/ml/predict` predice.

Docker / CI:

- Dockerfile multi-stage con `python:3.11.9-slim-bookworm`.
- `docker-compose.yml` para entorno local.
- GitHub Actions ejecuta compile, entrenamiento base, seed de SQLite, tests y build Docker.

## 4. Preguntas probables

Por que EWMA y GARCH?

- EWMA es rapido y transparente, util como benchmark de volatilidad.
- GARCH captura persistencia de volatilidad condicional y permite comparar modelos por AIC/BIC.

Por que ARCH-LM?

- Evalua si queda heterocedasticidad ARCH remanente en residuos. Si queda, el modelo aun no captura completamente la dinamica de varianza.

Por que Nelson-Siegel?

- Resume una curva de tasas completa con nivel, pendiente y curvatura, y permite interpolar tasas para distintos vencimientos.

Por que convexidad?

- La duracion modificada es una aproximacion lineal. La convexidad corrige la curvatura precio-tasa y mejora la aproximacion ante shocks grandes.

Por que Markowitz long-only?

- Porque la rubrica exige no negatividad. Es tambien una restriccion realista para inversionistas sin short selling.

Por que comparar con short selling?

- Para mostrar el efecto metodologico de relajar la restriccion. No implica que sea una recomendacion para el usuario.

Por que SQLite?

- Es suficiente para el proyecto, portable y compatible con SQLAlchemy ORM. El ORM permite migrar luego a PostgreSQL con menos cambios.

## 5. Checklist antes de presentar

- Ejecutar `pytest -q`.
- Verificar `/health`.
- Abrir `/docs` y `/redoc`.
- Verificar que Streamlit apunte al backend correcto.
- Ejecutar al menos una vez GARCH, Markowitz, renta fija, opciones, stress y ML.
- Tener configuradas claves reales si se va a mostrar IA o FRED en vivo.
- Tener alternativa local explicada si FRED o proveedor externo no responde.

