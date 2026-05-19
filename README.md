# Portafolio Riesgo USTA

Backend FastAPI y dashboard Streamlit para analisis integral de portafolios financieros, teoria del riesgo, valoracion de activos, optimizacion, Machine Learning, RoboAdvisor, KYC, stress testing y automatizacion institucional Perri.

El proyecto permite consultar activos, precios historicos, rendimientos, indicadores tecnicos, VaR/CVaR, CAPM, Markowitz, GARCH, senales tecnicas, analisis macroeconomico, benchmark, renta fija, opciones, stress testing, Machine Learning y RoboAdvisor con persistencia en SQLite.

---

## 1. Objetivo del proyecto

Construir una arquitectura modular, reproducible y desplegable para analizar portafolios financieros internacionales desde una perspectiva cuantitativa, estadistica y de riesgo.

El sistema esta dividido en dos capas principales:

- Backend FastAPI: concentra logica financiera, validacion, persistencia, servicios de negocio, endpoints, jobs, automatizacion, Machine Learning, Docker, CI/CD y pruebas.
- Frontend Streamlit: consume la API y presenta modulos visuales para interpretacion financiera y toma de decisiones.

---

## 2. Estado tecnico actual

El proyecto incluye actualmente:

- FastAPI modular.
- Streamlit modular.
- Pydantic v2.
- Pydantic Settings.
- SQLAlchemy 2.x.
- SQLite local.
- Persistencia de activos.
- Persistencia de precios historicos.
- Lectura de precios desde SQLite con fallback a proveedor externo.
- Universo Perri institucional.
- Optimizacion automatica de Perri con horizontes 1y, 3y y 5y.
- Portafolios Perri de 5, 10 y 15 activos.
- Objetivos Perri: min_risk, max_sharpe y max_return.
- Job para guardar la ultima optimizacion en JSON.
- GitHub Actions para CI.
- GitHub Actions programado para actualizacion de Perri.
- Dockerfile del backend.
- docker-compose.yml.
- Tests con pytest y TestClient.
- Machine Learning con train, joblib, Singleton y endpoint predictivo.
- Modelo ML persistido en backend/app/ml/model.joblib.
- Endpoints /api/v1/ml/status y /api/v1/ml/predict.
- Nelson-Siegel para curva de rendimiento.
- Metricas de bono: precio, duracion Macaulay, duracion modificada y convexidad.
- Black-Scholes para opciones europeas.
- Cinco Greeks: delta, gamma, vega, theta y rho.
- Paridad put-call validada por test.
- Stress testing con shocks de tasa, mercado y volatilidad.
- CAPM.
- Markowitz.
- VaR/CVaR.
- Backtesting Kupiec.
- GARCH.
- Macro y benchmark.
- RoboAdvisor.
- Login basico.
- KYC / preferencias de inversionista.
- Dashboard Streamlit con paginas 0 a 12.

Pendiente o parcial:

- Deploy final backend.
- Deploy final frontend.
- Chatbot con IA externa integrada.
- Admin dashboard completo.
- Roles robustos.
- Reportes PDF.
- Informe ejecutivo final.

---

## 3. Estructura general

```text
portafolio-riesgo/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── router.py
│   │   │   └── v1/
│   │   ├── clients/
│   │   ├── core/
│   │   ├── db/
│   │   ├── domain/
│   │   ├── jobs/
│   │   ├── ml/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── data/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── .streamlit/
│   ├── assets/
│   ├── pages/
│   ├── services/
│   ├── ui/
│   ├── app.py
│   ├── config.py
│   └── requirements.txt
├── tests/
├── docs/
├── .github/workflows/
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── .gitignore
├── roboadvisor_cache.csv
└── README.md
```

---

## 4. Tecnologias principales

### Backend

- Python 3.11 recomendado.
- FastAPI.
- Uvicorn.
- Pydantic.
- Pydantic Settings.
- SQLAlchemy.
- SQLite.
- pandas.
- numpy.
- scipy.
- yfinance.
- arch.
- scikit-learn.
- joblib.
- pytest.
- httpx.

### Frontend

- Streamlit.
- Plotly.
- pandas.
- numpy.
- requests.

### DevOps

- Docker.
- Docker Compose.
- GitHub Actions.
- Streamlit Cloud para frontend.
- Render o Railway sugerido para backend.

---

## 5. Arquitectura del backend

El backend esta organizado por responsabilidades:

```text
backend/app/
├── api/          # Routers FastAPI
├── clients/      # Clientes externos: mercado y macro
├── core/         # Configuracion, seguridad, excepciones y dependencias
├── db/           # SQLAlchemy, modelos, seeders e importadores
├── domain/       # Constantes o reglas de dominio
├── jobs/         # Jobs ejecutables manualmente o por GitHub Actions
├── ml/           # Entrenamiento, modelo joblib y predictor Singleton
├── schemas/      # Contratos Pydantic
├── services/     # Logica de negocio y modelos financieros
└── main.py       # Entrada principal FastAPI
```

Regla de diseno:

```text
Routers reciben y responden.
Schemas validan.
Services calculan.
Clients consultan proveedores externos.
DB persiste.
Jobs automatizan procesos.
Frontend visualiza.
```

---

## 6. Entrada principal FastAPI

Archivo:

```text
backend/app/main.py
```

Responsabilidades:

- Crear instancia FastAPI.
- Configurar CORS.
- Inicializar SQLite mediante lifespan.
- Registrar manejador de excepciones.
- Registrar endpoint raiz.
- Registrar health check.
- Montar api_router.

Endpoints base:

```text
GET /
GET /health
```

Documentacion local:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/redoc
```

---

## 7. Variables de entorno

Usar `.env.example` como plantilla.

Variables principales:

```text
APP_ENV
DEBUG
DATABASE_URL
ALLOWED_ORIGINS
INTERNAL_API_KEY
FRED_API_KEY
ALPHAVANTAGE_API_KEY
BACKEND_BASE_URL
BACKEND_API_PREFIX
BACKEND_TIMEOUT_SECONDS
```

En Streamlit Cloud, configurar secrets:

```toml
BACKEND_BASE_URL = "URL_PUBLICA_BACKEND"
BACKEND_API_PREFIX = "/api/v1"
BACKEND_TIMEOUT_SECONDS = "30"
INTERNAL_API_KEY = "valor_seguro"
```

No subir archivos `.env` ni `frontend/.streamlit/secrets.toml`.

---

## 8. Routers disponibles

Prefijo general:

```text
/api/v1
```

Routers principales:

```text
/api/v1/assets
/api/v1/market
/api/v1/technical
/api/v1/risk
/api/v1/portfolio
/api/v1/macro
/api/v1/capm
/api/v1/decision
/api/v1/investor
/api/v1/benchmark
/api/v1/help
/api/v1/returns-stats
/api/v1/alerts
/api/v1/garch
/api/v1/valuation
/api/v1/stress
/api/v1/ml
/api/v1/roboadvisor
/api/v1/perri
/api/v1/persistence
/api/v1/chatbot
```

---

## 9. Endpoints relevantes

### Root y health

```text
GET /
GET /health
```

### Machine Learning

```text
GET  /api/v1/ml/status
POST /api/v1/ml/predict
```

### Renta fija

```text
POST /api/v1/valuation/nelson-siegel
POST /api/v1/valuation/bond-metrics
```

### Opciones

```text
POST /api/v1/valuation/black-scholes
```

### Stress testing

```text
POST /api/v1/stress/scenario
```

### Perri

```text
GET /api/v1/perri/latest
GET /api/v1/perri/optimize
```

### RoboAdvisor

```text
POST /api/v1/roboadvisor/suggest
```

---

## 10. Persistencia con SQLAlchemy y SQLite

Archivos principales:

```text
backend/app/db/database.py
backend/app/db/models.py
backend/app/db/seed_db.py
backend/app/db/import_perri_prices.py
```

La ruta SQLite se resuelve de forma estable a:

```text
backend/data/portafolio_riesgo.db
```

Modelos relevantes:

```text
Asset
Price
Portfolio
PredictionLog
```

La tabla prices guarda informacion metodologica como:

```text
close_original
original_currency
fx_ticker
fx_rate_to_usd
close_usd
close
source
```

---

## 11. Perri institucional

Perri es el componente institucional de optimizacion automatica construido sobre SQLite.

Archivos:

```text
backend/app/services/perri_optimizer_service.py
backend/app/api/v1/perri.py
backend/app/jobs/run_perri_optimization.py
backend/data/perri_latest_optimization.json
```

Responsabilidades:

- Leer activos elegibles desde SQLite.
- Filtrar activos por clase.
- Construir retornos historicos.
- Optimizar portafolios exactos de 5, 10 y 15 activos.
- Calcular horizontes de 1, 3 y 5 anos.
- Optimizar min_risk, max_sharpe y max_return.
- Generar metricas de retorno esperado, volatilidad, Sharpe, beta, alpha y distribucion por clase de activo.

---

## 12. Modelos financieros implementados

### Markowitz

Incluye:

- Frontera eficiente.
- Portafolio de minima varianza.
- Portafolio de maximo Sharpe.
- Matriz de correlacion.
- Portafolio objetivo.
- Ranking de portafolios.

### CAPM

Incluye:

- Beta.
- Alpha.
- R cuadrado.
- Retorno esperado.
- CAPM por activo.
- CAPM por portafolio.

### VaR/CVaR

Incluye:

- VaR historico.
- VaR parametrico.
- VaR Monte Carlo.
- CVaR.
- Test de Kupiec.

### GARCH

Incluye:

- ARCH.
- GARCH.
- EGARCH.
- Comparacion AIC/BIC.
- Diagnostico.
- Pronostico de volatilidad.

### Nelson-Siegel y renta fija

Incluye:

- Curva Nelson-Siegel.
- Precio teorico de bono.
- Duracion Macaulay.
- Duracion modificada.
- Convexidad.

### Black-Scholes

Incluye:

- Precio teorico de call y put.
- Delta.
- Gamma.
- Vega.
- Theta.
- Rho.
- Validacion de paridad put-call.

### Stress testing

Incluye:

- Shock de tasa.
- Shock de mercado.
- Multiplicador de volatilidad.
- Retorno estresado.
- Volatilidad estresada.
- VaR estresado.
- Perdida estimada.
- Valor del portafolio bajo stress.
- Severidad.

### Machine Learning

Incluye:

- Script de entrenamiento.
- Modelo joblib.
- Predictor Singleton.
- Endpoint de estado.
- Endpoint de prediccion.
- Tests de carga y prediccion.

---

## 13. Frontend Streamlit

Estructura:

```text
frontend/app.py
frontend/config.py
frontend/pages/
frontend/services/api_client.py
frontend/ui/
```

Paginas del dashboard:

```text
0_Contextualizacion.py
01_Tecnico.py
02_Rendimientos.py
03_Garch.py
04_Capm.py
05_Var_Cvar.py
06_Markowitz.py
07_Senales.py
08_Macro_Benchmark.py
09_Renta_Fija.py
10_Opciones.py
11_Stress_Testing.py
12_Machine_Learning.py
```

---

## 14. Modulos del dashboard

### Modulo 0 - Contextualizacion

Muestra universo de activos, activos base, activos ampliados, metadata de Perri, clase de activo, benchmark metodologico, fuente, tasa libre de riesgo y benchmark global.

### Modulo 1 - Tecnico

Incluye precio, SMA, EMA, RSI, Bollinger, MACD y estocastico.

### Modulo 2 - Rendimientos

Incluye rendimientos simples y logaritmicos, estadisticas descriptivas, histograma, boxplot, Q-Q plot y pruebas de normalidad.

### Modulo 3 - GARCH

Incluye ARCH, GARCH, EGARCH, diagnostico y pronostico.

### Modulo 4 - CAPM

Incluye beta, alpha, R cuadrado, p-value y retorno esperado.

### Modulo 5 - VaR/CVaR

Incluye VaR historico, parametrico, Monte Carlo, CVaR, riesgo monetario y backtesting.

### Modulo 6 - Markowitz

Incluye frontera eficiente, minima varianza, maximo Sharpe, retorno objetivo, matriz de correlacion y perfiles.

### Modulo 7 - Senales

Incluye senales tecnicas por RSI, MACD, Bollinger, medias moviles y estocastico.

### Modulo 8 - Macro y Benchmark

Incluye tasa libre de riesgo, FX spot, comparacion contra benchmark, alpha de Jensen, tracking error, information ratio y drawdown.

### Modulo 9 - Renta Fija

Incluye Nelson-Siegel, curva de tasas, precio de bono, duracion y convexidad.

### Modulo 10 - Opciones

Incluye Black-Scholes, precio teorico, cinco Greeks, payoff y analisis de sensibilidad.

### Modulo 11 - Stress Testing

Incluye escenarios adversos, perdida estimada, valor estresado, severidad y comparacion grafica.

### Modulo 12 - Machine Learning

Incluye estado del modelo, prediccion de retorno esperado y sensibilidad por volatilidad.

---

## 15. Tests

Ejecutar toda la suite:

```powershell
$env:PYTHONPATH="backend"
python -m pytest tests -v
```

Validaciones actuales:

- Chatbot.
- Perri.
- Portfolio/Perri comparison.
- Machine Learning.
- Renta fija.
- Opciones.
- Stress testing.
- Riesgo.
- CAPM.
- Markowitz.
- GARCH.
- Nelson-Siegel.
- Black-Scholes.
- KYC/RoboAdvisor.

---

## 16. GitHub Actions

Workflow principal:

```text
.github/workflows/backend-ci.yml
```

Valida:

- Instalacion de dependencias.
- Compilacion del backend.
- Entrenamiento del modelo ML base.
- Preparacion de SQLite/Perri.
- Ejecucion de tests.
- Build Docker del backend.

Workflow programado Perri:

```text
.github/workflows/perri-scheduled-update.yml
```

---

## 17. Docker

Archivos:

```text
backend/Dockerfile
docker-compose.yml
.dockerignore
```

Build:

```powershell
docker compose build backend
```

Levantar backend:

```powershell
docker compose up backend
```

Puerto local Docker:

```text
http://127.0.0.1:8001
```

Probar health:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8001/health"
```

---

## 18. Instalacion local

Clonar repositorio:

```powershell
git clone https://github.com/edwardmorarom/Portafolio_APIS_RIESGO.git
cd Portafolio_APIS_RIESGO
```

Crear entorno virtual:

```powershell
python -m venv .venv
```

Activar entorno virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instalar backend:

```powershell
pip install -r backend
equirements.txt
```

Instalar frontend:

```powershell
pip install -r frontend
equirements.txt
```

---

## 19. Ejecucion local

Backend:

```powershell
$env:PYTHONPATH="backend"
uvicorn app.main:app --reload --app-dir backend
```

Frontend:

```powershell
streamlit run frontend/app.py
```

---

## 20. Preparacion de datos Perri

Desde la raiz:

```powershell
$env:PYTHONPATH="backend"
python -m app.db.seed_db
python -m app.db.import_perri_prices
python -m app.jobs.run_perri_optimization
```

---

## 21. Validacion rapida

```powershell
$env:PYTHONPATH="backend"
python -m compileall backendpp
python -m compileall frontend
python -m pytest tests -v
```

---

## 22. Archivos que no deben versionarse

No subir:

```text
.env
backend/.env
frontend/.streamlit/secrets.toml
*.db
*.sqlite
*.sqlite3
.venv/
.pytest_cache/
__pycache__/
```

Si subir:

```text
.gitignore
.env.example
frontend/requirements.txt
backend/requirements.txt
docs/
.github/workflows/
```

---

## 23. Documentacion complementaria

Documentos recomendados:

```text
docs/01_arquitectura_tecnica.md
docs/02_endpoints_backend_frontend.md
```

---

## 24. Deploy

Backend sugerido:

- Render.
- Railway.
- Docker en servidor.

Frontend sugerido:

- Streamlit Cloud.

Flujo recomendado:

```text
Editar codigo local
git add .
git commit
git push origin backend
redeploy automatico en plataforma conectada
```

---

## 25. Buenas practicas del proyecto

Antes de cada commit:

```powershell
git status
python -m compileall backendpp
python -m compileall frontend
$env:PYTHONPATH="backend"
python -m pytest tests -v
```

Patron recomendado:

```text
1. Revisar estado real del codigo.
2. Hacer un cambio puntual.
3. Compilar.
4. Probar endpoint o script.
5. Ejecutar tests si aplica.
6. Revisar git status.
7. Hacer commit descriptivo.
8. Hacer push.
```

---

## 26. Comandos Git frecuentes

```powershell
git status
git add <archivo>
git commit -m "mensaje claro"
git push origin backend
```

Ejemplo:

```powershell
git add README.md
git commit -m "Actualiza README del proyecto" -m "Documenta arquitectura, endpoints, modulos, despliegue, validacion y estado tecnico actual."
git push origin backend
```

---

## 27. Autores

- Edward Mora.
- Juan P. Vargas.

---

## 28. Nota metodologica

El proyecto trabaja sobre una moneda base comun, USD, para evitar errores metodologicos al comparar activos internacionales.

Perri usa precios persistidos en SQLite, no calculos improvisados en frontend. Esto permite reproducibilidad, automatizacion y trazabilidad.

Machine Learning se implementa como componente backend reproducible mediante entrenamiento, persistencia del modelo y consumo por endpoint.
