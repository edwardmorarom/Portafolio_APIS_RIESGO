# Cierre de Rubrica - Proyecto Integrador Riesgo Python CIII

Fecha de revision: 2026-05-22

Este documento resume como queda evidenciado cada bloque de la rubrica en el repositorio. No reemplaza la sustentacion oral, pero deja una guia tecnica para revisar codigo, frontend, backend y pruebas.

## Criterios financieros

1. Analisis tecnico:
   - Frontend: `frontend/pages/01_Tecnico.py`.
   - Evidencia: SMA, EMA, RSI, MACD, Bollinger y oscilador estocastico con Plotly y filtros por activo del portafolio.

2. Rendimientos:
   - Frontend: `frontend/pages/02_Rendimientos.py`.
   - Backend: endpoints de mercado y retornos.
   - Evidencia: usa activos, pesos, horizonte y benchmark de la configuracion inicial.

3. EWMA, ARCH, GARCH y EGARCH:
   - Backend: `backend/app/services/garch_service.py`, `backend/app/api/v1/garch.py`.
   - Frontend: `frontend/pages/03_Garch.py`.
   - Evidencia: compara ARCH/GARCH/EGARCH, distribucion normal/t-Student y agrega EWMA como referencia de volatilidad con lambda configurable.

4. CAPM:
   - Backend: `backend/app/api/v1/capm.py`, `backend/app/services/capm_service.py`.
   - Evidencia: beta, alpha de Jensen, R2, retorno esperado y benchmark dinamico del portafolio.

5. VaR, CVaR y Kupiec:
   - Backend: `backend/app/services/risk_service.py`.
   - Tests: `tests/test_var_kupiec.py`.
   - Evidencia: Kupiec separado para VaR historico, parametrico y Monte Carlo. CVaR queda como severidad complementaria, no como objeto directo de Kupiec.

6. Markowitz:
   - Backend: `backend/app/services/portfolio_service.py`.
   - Frontend: `frontend/pages/06_Markowitz.py`.
   - Evidencia: simulacion de 10,000+ portafolios como conjunto factible, matriz de correlacion, frontera eficiente resuelta por QP/SLSQP sobre grilla de retornos objetivo, optimizacion de minima varianza y maximo Sharpe, comparacion con y sin short selling metodologico en el mismo grafico, costo de imponer no negatividad y activos con peso cero.

7. Renta fija:
   - Backend: `backend/app/api/v1/fixed_income.py`, `backend/app/services/yield_service.py`, `backend/app/clients/macro_client.py`.
   - Frontend: `frontend/pages/09_Renta_Fija.py`.
   - Evidencia: Nelson-Siegel, precio, duracion, duracion modificada, convexidad, sensibilidad ante shocks de +/-50, +/-100 y +/-200 pb con aproximacion lineal, duracion + convexidad y repricing exacto, compra de bono TES y curva Treasury desde FRED con fallback marcado.

8. Opciones:
   - Backend: `backend/app/api/v1/valuation.py`.
   - Frontend: `frontend/pages/10_Opciones.py`.
   - Evidencia: Black-Scholes, Greeks, payoff, sensibilidad y subyacente sugerido desde activos del portafolio.

9. Stress testing:
   - Backend: `backend/app/api/v1/stress.py`, `backend/app/services/stress_service.py`.
   - Tests: `tests/test_stress_testing.py`.
   - Evidencia: escenario base, shocks, perdida de portafolio, comparacion benchmark e interpretacion.

## Criterios tecnicos

10. Backend FastAPI, Pydantic y SQLAlchemy:
   - Routers: `backend/app/api/v1`.
   - Schemas: `backend/app/schemas`.
   - Servicios: `backend/app/services`.
   - Persistencia: `backend/app/db/models.py`, `backend/app/db/database.py`.
   - Evidencia nueva: endpoints `POST/GET /api/v1/portfolio/saved` para persistir portafolios; `PredictionLog` se alimenta desde `/api/v1/ml/predict`.

11. Machine Learning:
   - Backend: `backend/app/ml/predictor.py`, `backend/app/api/v1/ml.py`.
   - Frontend: `frontend/pages/12_Machine_Learning.py`.
   - Evidencia: predictor Singleton, modelo joblib, endpoint `/api/v1/ml/predict`, target de retorno acumulado a horizonte fijo con Ridge, Lasso y Gradient Boosting.

12. Tests pytest + TestClient:
   - Carpeta: `tests`.
   - Evidencia nueva: `tests/test_rubric_backend_closure.py` cubre EWMA, curva Treasury, persistencia de portafolio y log de predicciones.
   - Comando: `pytest`.

13. Docker, deploy y CI:
   - Docker: `backend/Dockerfile`, `docker-compose.yml`.
   - CI: `.github/workflows/backend-ci.yml`.
   - Actualizacion programada: `.github/workflows/perri-scheduled-update.yml`.
   - PaaS: `render.yaml`.
   - Nota: el despliegue publico depende de configurar secretos reales en Render/GitHub (`INTERNAL_API_KEY`, `GROQ_API_KEY`, `FRED_API_KEY`) y URL final del frontend en `ALLOWED_ORIGINS`.

14. Frontend:
   - Streamlit modular en `frontend/pages`.
   - Evidencia: helper de filtros, chips/toggles, Plotly institucional, estado global de portafolio y ayudas contextuales.

15. Buenas practicas:
   - Separacion por routers, schemas, services, clients y frontend services.
   - `.env.example` documenta variables sin exponer secretos.

16. Sustentacion:
   - Reporte PDF: `backend/app/api/v1/reports.py`, `backend/app/services/pdf_service.py`, `frontend/pages/14_Reportes.py`.
   - Evidencia: reporte ejecutivo de maximo 5 secciones: riesgo, metodologia, arquitectura, resultados numericos y conclusiones/recomendaciones.

## Validacion sugerida

```powershell
python -m compileall backend frontend tests
pytest
```

## Dependencias de entorno real

- Chatbot IA: configurar `LLM_PROVIDER=groq`, `GROQ_API_KEY` y opcionalmente `LLM_MODEL=llama-3.1-8b-instant`.
- FRED: configurar `FRED_API_KEY` para curva Treasury real. Sin clave, el backend retorna fallback identificado como `fallback_local`.
- Deploy: configurar secretos en Render/GitHub y actualizar `ALLOWED_ORIGINS` con la URL publica del frontend.
