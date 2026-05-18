# Portafolio Riesgo USTA

Backend FastAPI y dashboard Streamlit para análisis integral de portafolios financieros, teoría del riesgo, valoración, optimización y automatización institucional de Perri.

El proyecto permite consultar activos, precios históricos, rendimientos, indicadores técnicos, VaR/CVaR, CAPM, Markowitz, GARCH, señales técnicas, análisis macroeconómico, benchmark, RoboAdvisor y optimización automática de portafolios con persistencia en SQLite.

---

## 1. Objetivo del proyecto

Construir una arquitectura modular y reproducible para analizar portafolios financieros internacionales desde una perspectiva cuantitativa, estadística y de riesgo.

El sistema está dividido en dos capas principales:

- **Backend FastAPI**: concentra lógica financiera, validación, persistencia, servicios de negocio, endpoints, jobs, automatización y pruebas.
- **Frontend Streamlit**: consume la API y presenta módulos visuales para interpretación financiera y toma de decisiones.

---

## 2. Estado técnico actual

El proyecto incluye actualmente:

- FastAPI modular.
- Streamlit modular.
- Pydantic y Pydantic Settings.
- SQLAlchemy 2.x.
- SQLite local.
- Persistencia de activos.
- Persistencia de precios históricos.
- Lectura de precios desde SQLite con fallback a proveedor externo.
- Universo Perri institucional.
- Optimización automática de Perri.
- Job para guardar la última optimización en JSON.
- GitHub Actions para CI.
- GitHub Actions programado para actualización de Perri.
- Dockerfile del backend.
- `docker-compose.yml`.
- Tests con `pytest` y `TestClient`.
- Nelson-Siegel.
- Black-Scholes.
- CAPM.
- Markowitz.
- VaR/CVaR.
- GARCH.
- RoboAdvisor.
- Dashboard Streamlit.
- Login básico.
- KYC / preferencias de inversionista.

Pendiente o parcial:

- ML Singleton predictivo real con endpoint `/predict`.
- Admin dashboard completo.
- Reportes PDF.
- Roles robustos.
- Deploy PaaS final.
- Más pruebas unitarias por módulo.
- Validación final del runtime Docker con `/health`.

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
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── data/
│   ├── requirements.txt
│   ├── runtime.txt
│   ├── update_cache.py
│   └── Dockerfile
├── frontend/
│   ├── pages/
│   ├── services/
│   ├── ui/
│   ├── app.py
│   └── config.py
├── tests/
├── docs/
├── .github/workflows/
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── .gitignore
├── requirements.txt
├── roboadvisor_cache.csv
└── README.md
```

---

## 4. Tecnologías principales

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
- pytest.
- httpx.

### Frontend

- Streamlit.
- Plotly.
- pandas.
- requests.

### DevOps

- Docker.
- Docker Compose.
- GitHub Actions.

---

## 5. Arquitectura del backend

El backend está organizado por responsabilidades.

```text
backend/app/
├── api/          # Routers FastAPI
├── clients/      # Clientes externos: mercado y macro
├── core/         # Configuración, seguridad, excepciones, dependencias
├── db/           # SQLAlchemy, modelos, seeders e importadores
├── jobs/         # Jobs ejecutables manualmente o por GitHub Actions
├── schemas/      # Contratos Pydantic
├── services/     # Lógica de negocio y modelos financieros
└── main.py       # Entrada principal FastAPI
```

Regla de diseño:

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

- Crear instancia `FastAPI`.
- Configurar CORS.
- Inicializar SQLite mediante `lifespan`.
- Registrar manejador de excepciones.
- Registrar endpoint raíz.
- Registrar health check.
- Montar `api_router`.

Endpoints base:

```text
GET /
GET /health
```

La inicialización de base de datos usa:

```text
init_db()
```

Esto crea las tablas SQLAlchemy al iniciar la aplicación.

---

## 7. Configuración

Archivo:

```text
backend/app/core/settings.py
```

Clase principal:

```python
class Settings(BaseSettings)
```

Variables principales:

```env
APP_NAME=Portafolio Riesgo API
APP_VERSION=0.1.0
APP_ENV=dev
DEBUG=true
API_V1_PREFIX=/api/v1
DATABASE_URL=sqlite:///./data/portafolio_riesgo.db
DEFAULT_START_DATE=2021-01-01
DEFAULT_END_DATE=2026-12-31
GLOBAL_BENCHMARK=ACWI
DEFAULT_BASE_CURRENCY=USD
FRED_API_KEY=
FRONTEND_BASE_URL=http://localhost:8501
ALLOWED_ORIGINS=http://localhost:8501,http://127.0.0.1:8501
MIN_OBS_VAR=60
MIN_OBS_CAPM=60
MIN_OBS_PORTFOLIO=60
```

El proyecto usa `get_settings()` con cache para evitar recrear configuración en cada request.

---

## 8. Variables de entorno

Crear `.env` desde `.env.example`.

En PowerShell:

```powershell
Copy-Item .env.example .env
Copy-Item .env backend\.env
```

No subir `.env` al repositorio.

---

## 9. Routers disponibles

Todos los routers se registran en:

```text
backend/app/api/router.py
```

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
/api/v1/roboadvisor
/api/v1/perri
/api/v1/persistence
```

---

## 10. Endpoints principales

### Root y health

```text
GET /
GET /health
```

### Assets

```text
GET /api/v1/assets/
GET /api/v1/assets/search?q={query}
GET /api/v1/assets/summary
```

### Market

```text
GET /api/v1/market/prices/{ticker}
GET /api/v1/market/returns/{ticker}
```

### Technical

```text
GET /api/v1/technical/indicators/{ticker}
```

### Returns Stats

```text
GET /api/v1/returns-stats/summary/{ticker}
```

### GARCH

```text
GET /api/v1/garch/{ticker}
```

### CAPM

```text
GET /api/v1/capm/{ticker}
POST /api/v1/capm/portfolio
```

### Risk

```text
POST /api/v1/risk/var
```

### Portfolio

```text
POST /api/v1/portfolio/efficient-frontier
```

### Benchmark

```text
POST /api/v1/benchmark/compare
```

### Macro

```text
GET /api/v1/macro/
GET /api/v1/macro/fx-spot/{base_currency}
```

### Decision

```text
POST /api/v1/decision/panel
```

### Investor

```text
POST /api/v1/investor/preferences
```

### Help

```text
GET /api/v1/help/catalog
```

### Alerts

```text
GET /api/v1/alerts/{ticker}
```

### Valuation

```text
POST /api/v1/valuation/nelson-siegel
POST /api/v1/valuation/black-scholes
```

### RoboAdvisor

```text
POST /api/v1/roboadvisor/suggest
```

### Perri

```text
GET /api/v1/perri/latest
GET /api/v1/perri/optimize
```

### Persistence

```text
GET /api/v1/persistence/health
```

---

## 11. Inyección de dependencias

Archivo:

```text
backend/app/core/dependencies.py
```

El proyecto usa `Depends` para conectar endpoints con servicios y clientes.

Ejemplo de flujo:

```text
Endpoint FastAPI
    ↓ Depends(get_market_service)
MarketService
    ↓ Depends(get_market_client)
MarketClient
    ↓ Depends(get_app_settings)
Settings
```

Dependencias relevantes:

```python
get_app_settings()
get_market_client()
get_macro_client()
get_market_service()
get_technical_service()
get_risk_service()
get_portfolio_service()
get_macro_service()
get_capm_service()
get_decision_service()
get_investor_service()
get_assets_service()
get_benchmark_service()
get_help_service()
get_returns_stats_service()
get_alerts_service()
get_garch_service()
get_db()
```

---

## 12. Persistencia con SQLAlchemy y SQLite

Archivos:

```text
backend/app/db/database.py
backend/app/db/models.py
backend/app/db/seed_db.py
backend/app/db/import_perri_prices.py
```

### database.py

Responsabilidades:

- Crear `Base`.
- Resolver ruta estable de SQLite.
- Crear `engine`.
- Crear `SessionLocal`.
- Exponer `get_db()`.
- Exponer `init_db()`.

La ruta SQLite se resolvió para apuntar de forma estable a:

```text
backend/data/portafolio_riesgo.db
```

Esto evita que se creen bases accidentales cuando los comandos se ejecutan desde la raíz, `backend/`, Docker o GitHub Actions.

### models.py

Modelos actuales:

```text
Asset
Price
Portfolio
PredictionLog
```

Relación principal:

```text
Asset 1 ─── N Price
```

La tabla `prices` guarda:

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

## 13. Universo de activos

El proyecto tiene activos base y universo Perri.

Archivos relacionados:

```text
backend/app/core/assets_registry.py
backend/app/db/build_perri_universe.py
backend/app/db/seed_db.py
backend/data/perri_universe.json
```

El universo Perri clasifica activos por:

```text
renta_variable
renta_fija
commodity
etf_global
etf_sectorial
efectivo_o_corto_plazo
```

También conserva metadata metodológica:

```text
moneda_origen
fx_ticker
benchmark_ticker
benchmark_description
include_in_perri
source
```

---

## 14. Precios históricos

Fuente actual:

```text
roboadvisor_cache.csv
```

Importador:

```text
backend/app/db/import_perri_prices.py
```

Flujo:

```text
roboadvisor_cache.csv
        ↓
import_perri_prices.py
        ↓
tabla prices
        ↓
MarketService
        ↓
/api/v1/market/prices/{ticker}
```

El sistema guarda el cierre original y el cierre convertido a USD. En el universo actual, la mayoría de activos de Perri se trabajan en USD, por lo que:

```text
fx_rate_to_usd = 1.0
close_usd = close_original
```

---

## 15. MarketService

Archivo:

```text
backend/app/services/market_service.py
```

Responsabilidad:

- Consultar precios desde SQLite primero.
- Usar `MarketClient` como respaldo si no hay datos persistidos.
- Calcular rendimientos simples y logarítmicos.

Flujo:

```text
GET /api/v1/market/prices/{ticker}
        ↓
MarketService.get_prices()
        ↓
_get_prices_from_db()
        ↓
Asset + Price
        ↓
Fallback a MarketClient si no hay datos
```

---

## 16. Conversión a USD

El proyecto trabaja con USD como moneda base metodológica.

En el flujo externo, `MarketClient` convierte precios internacionales a USD usando metadata de activo y series FX cuando corresponde.

Campos relevantes:

```text
Currency
BaseCurrency
FxTicker
FxRateToUSD
```

En SQLite se conserva:

```text
original_currency
fx_ticker
fx_rate_to_usd
close_usd
```

---

## 17. Perri institucional

Perri es el componente institucional de optimización automática construido sobre SQLite.

Archivos:

```text
backend/app/services/perri_optimizer_service.py
backend/app/api/v1/perri.py
backend/app/jobs/run_perri_optimization.py
backend/data/perri_latest_optimization.json
```

### PerriOptimizerService

Responsabilidades:

- Leer activos elegibles desde SQLite.
- Filtrar renta variable y renta fija.
- Construir retornos históricos.
- Seleccionar candidatos.
- Optimizar mínimo riesgo.
- Optimizar mejor relación riesgo-rentabilidad usando Sharpe.

Métodos principales:

```python
_get_date_window()
_load_eligible_assets()
_load_close_series()
_build_returns_by_asset()
_individual_metrics()
_build_aligned_returns_matrix()
_portfolio_metrics()
_optimize()
run_optimization()
```

### Endpoints Perri

```text
GET /api/v1/perri/latest
GET /api/v1/perri/optimize
```

`/latest` devuelve el JSON precalculado.

`/optimize` recalcula desde SQLite.

### Job Perri

Archivo:

```text
backend/app/jobs/run_perri_optimization.py
```

Genera:

```text
backend/data/perri_latest_optimization.json
```

Flujo:

```text
seed_db
    ↓
import_perri_prices
    ↓
run_perri_optimization
    ↓
perri_latest_optimization.json
```

---

## 18. Modelos financieros implementados

### Markowitz

Archivo:

```text
backend/app/services/portfolio_service.py
```

Incluye:

- Frontera eficiente.
- Portafolio de mínima varianza.
- Portafolio de máximo Sharpe.
- Matriz de correlación.
- Portafolio objetivo.
- Ranking de portafolios.

### CAPM

Archivo:

```text
backend/app/services/capm_service.py
```

Incluye:

- Beta.
- Alpha.
- R².
- Retorno esperado.
- CAPM por activo.
- CAPM por portafolio.

### VaR/CVaR

Archivo:

```text
backend/app/services/risk_service.py
```

Incluye:

- VaR histórico.
- VaR paramétrico.
- VaR Monte Carlo.
- CVaR.
- Test de Kupiec.

### GARCH

Archivo:

```text
backend/app/services/garch_service.py
```

Incluye:

- ARCH.
- GARCH.
- EGARCH.
- Comparación por AIC/BIC.
- Diagnóstico.
- Pronóstico de volatilidad.

### Nelson-Siegel

Archivo:

```text
backend/app/services/yield_service.py
```

Endpoint:

```text
POST /api/v1/valuation/nelson-siegel
```

### Black-Scholes

Archivo:

```text
backend/app/services/option_service.py
```

Endpoint:

```text
POST /api/v1/valuation/black-scholes
```

---

## 19. Schemas y validadores Pydantic

Ubicación:

```text
backend/app/schemas/
```

El proyecto usa:

```python
@field_validator(...)
@model_validator(...)
```

Validaciones principales:

- Tickers.
- Pesos.
- Suma de pesos.
- Tipo de retorno.
- Moneda base.
- Perfil de riesgo.
- Distribución.
- Horizonte de inversión.
- Alias enviados desde frontend.

Ejemplos de schemas:

```text
portfolio.py
risk.py
capm.py
benchmark.py
investor.py
garch.py
returns_stats.py
common.py
market.py
valuation.py
```

---

## 20. Seguridad básica

Archivo:

```text
backend/app/core/security.py
```

Función:

```python
require_internal_api_key()
```

Se usa en endpoints sensibles con:

```python
Depends(require_internal_api_key)
```

Módulos protegidos o parcialmente protegidos:

```text
benchmark
capm portfolio
decision
portfolio
risk
```

---

## 21. Manejo de errores

Archivos:

```text
backend/app/core/error_catalog.py
backend/app/core/exceptions.py
```

Excepciones principales:

```text
AppBaseException
InvalidDateRangeError
FutureDateError
InvalidApiKeyError
TickerNotFoundError
InsufficientObsVarError
InsufficientObsCapmError
InsufficientObsPortfolioError
ExternalApiFailureError
```

`main.py` registra un handler global para `AppBaseException`.

---

## 22. Decoradores

Archivo:

```text
backend/app/core/decorators.py
```

Decorador actual:

```python
log_execution_time(func)
```

Se usa para medir tiempo de ejecución en funciones sensibles, especialmente llamadas de mercado.

---

## 23. Frontend Streamlit

Ubicación:

```text
frontend/
```

Estructura:

```text
frontend/app.py
frontend/config.py
frontend/pages/
frontend/services/api_client.py
frontend/ui/
```

### Módulos del dashboard

```text
0_Contextualizacion.py
01_Tecnico.py
02_Rendimientos.py
03_Garch.py
04_Capm.py
05_Var_Cvar.py
06_Markowitz.py
07_Señales.py
08_Macro_Benchmark.py
```

### ApiClient

Archivo:

```text
frontend/services/api_client.py
```

Centraliza llamadas al backend.

Métodos relevantes:

```text
get_assets
search_assets
get_prices
get_returns
get_technical_indicators
get_returns_stats
get_alerts
get_garch
get_capm
get_portfolio_capm
post_var_risk
post_efficient_frontier
get_macro_snapshot
post_benchmark_compare
get_decision_panel
validate_investor_preferences
post_roboadvisor_suggest
```

---

## 24. Módulos del dashboard

### Módulo 0 - Contextualización

Muestra:

- Universo de activos.
- Activos base.
- Activos ampliados.
- Metadata de Perri.
- Clase de activo.
- Benchmark metodológico.
- Fuente.
- Tasa libre de riesgo.
- Benchmark global.

### Módulo 1 - Técnico

Incluye:

- Precio.
- SMA.
- EMA.
- RSI.
- Bollinger.
- MACD.
- Estocástico.

### Módulo 2 - Rendimientos

Incluye:

- Rendimientos simples y logarítmicos.
- Estadísticas descriptivas.
- Histograma.
- Boxplot.
- Q-Q plot.
- Pruebas de normalidad.

### Módulo 3 - GARCH

Incluye:

- ARCH.
- GARCH.
- EGARCH.
- Diagnóstico.
- Pronóstico.

### Módulo 4 - CAPM

Incluye:

- Beta.
- Alpha.
- R².
- P-value.
- Retorno esperado.

### Módulo 5 - VaR/CVaR

Incluye:

- VaR histórico.
- VaR paramétrico.
- VaR Monte Carlo.
- CVaR.
- Riesgo monetario.
- Backtesting.

### Módulo 6 - Markowitz

Incluye:

- Frontera eficiente.
- Mínima varianza.
- Máximo Sharpe.
- Retorno objetivo.
- Matriz de correlación.
- Perfiles.

### Módulo 7 - Señales

Incluye señales técnicas por:

- RSI.
- MACD.
- Bollinger.
- Medias móviles.
- Estocástico.

### Módulo 8 - Macro y Benchmark

Incluye:

- Tasa libre de riesgo.
- Inflación si existe FRED.
- FX spot.
- Comparación contra benchmark.
- Alpha de Jensen.
- Tracking error.
- Information ratio.
- Drawdown.

---

## 25. Tests

Ubicación:

```text
tests/
```

Tests actuales:

```text
tests/test_perri_latest.py
tests/test_perri_optimize.py
```

Ejecutar:

```powershell
python -m pytest tests/test_perri_latest.py tests/test_perri_optimize.py -q
```

Validan:

- `/api/v1/perri/latest`.
- `/api/v1/perri/optimize`.
- JSON precalculado.
- Optimización desde SQLite.
- Pesos de portafolio.
- Volatilidades no negativas.
- Suma de pesos cercana a 1.

---

## 26. GitHub Actions

Ubicación:

```text
.github/workflows/
```

Workflows actuales:

```text
backend-ci.yml
perri-scheduled-update.yml
```

### Backend CI

Ejecuta:

- Instalación de dependencias.
- `compileall` del backend.
- Preparación de SQLite.
- Importación de precios.
- Optimización Perri.
- Tests de Perri.

### Actualización automática Perri

Ejecuta dos veces al día:

```text
04:30 Colombia = 09:30 UTC
17:30 Colombia = 22:30 UTC
```

Flujo:

```text
seed_db
import_perri_prices
run_perri_optimization
validar JSON
commit automático del JSON actualizado
```

---

## 27. Docker

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

Probar health:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/health"
```

Resultado esperado:

```text
status : ok
env    : docker
```

---

## 28. Instalación local

### 1. Clonar repositorio

```bash
git clone https://github.com/edwardmorarom/Portafolio_APIS_RIESGO.git
cd Portafolio_APIS_RIESGO
```

### 2. Crear entorno virtual

```powershell
python -m venv .venv
```

### 3. Activar entorno virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Instalar dependencias

Desde la raíz:

```powershell
pip install -r requirements.txt
```

O desde backend:

```powershell
cd backend
pip install -r requirements.txt
```

Recomendación: usar Python 3.11 para evitar incompatibilidades de paquetes científicos.

---

## 29. Ejecución local

### Backend

```powershell
cd C:\Users\edwar\Desktop\portafolio-riesgo\backend
uvicorn app.main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Health:

```text
http://127.0.0.1:8000/health
```

### Frontend

Desde la raíz:

```powershell
streamlit run frontend/app.py
```

URL:

```text
http://localhost:8501
```

---

## 30. Preparación de datos Perri

Desde `backend`:

```powershell
cd C:\Users\edwar\Desktop\portafolio-riesgo\backend

python -m app.db.seed_db
python -m app.db.import_perri_prices
python -m app.jobs.run_perri_optimization
```

Esto deja lista:

```text
backend/data/perri_latest_optimization.json
```

---

## 31. Validación rápida

Desde la raíz:

```powershell
python -m compileall backend\app
python -m pytest tests\test_perri_latest.py tests\test_perri_optimize.py -q
```

Desde backend:

```powershell
uvicorn app.main:app --reload
```

Probar:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/v1/perri/latest"
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/v1/perri/optimize?history_years=5&rf_annual=0.04"
```

---

## 32. Archivos que no deben versionarse

El `.gitignore` excluye bases locales y archivos sensibles.

No subir:

```text
.env
*.db
*.sqlite
*.sqlite3
backend/data/*.db
data/*.db
.venv/
.pytest_cache/
__pycache__/
```

Sí se deben subir:

```text
.gitignore
.env.example
backend/data/perri_universe.json
backend/data/perri_latest_optimization.json
docs/
.github/workflows/
```

---

## 33. Documentación complementaria

Documentos recomendados dentro de `docs/`:

```text
docs/00_snapshot_codigo_actual.md
docs/01_arquitectura_tecnica.md
```

`00_snapshot_codigo_actual.md` sirve como inventario técnico generado desde el código.

`01_arquitectura_tecnica.md` explica la arquitectura, módulos, dependencias, decoradores y relaciones internas.

---

## 34. Buenas prácticas del proyecto

Antes de cada commit:

```powershell
git status
python -m compileall backend\app
python -m pytest tests\test_perri_latest.py tests\test_perri_optimize.py -q
```

Patrón recomendado:

```text
1. Revisar estado real del código.
2. Hacer un cambio puntual.
3. Compilar.
4. Probar endpoint o script.
5. Ejecutar tests si aplica.
6. Revisar git status.
7. Hacer commit descriptivo.
8. Hacer push.
```

---

## 35. Comandos Git frecuentes

```powershell
git status
git add <archivo>
git commit -m "mensaje: descripción clara del cambio"
git push origin backend
```

Ejemplo:

```powershell
git add backend/app/services/perri_optimizer_service.py
git commit -m "mejora: ajusta optimización institucional de Perri"
git push origin backend
```

---

## 36. Autores

- Edward Mora.
- Juan P. Vargas.

---

## 37. Nota metodológica

El proyecto trabaja sobre una moneda base común, USD, para evitar errores metodológicos al comparar activos internacionales. Los precios históricos se conservan con información de moneda original, tasa FX y cierre convertido.

La optimización institucional de Perri usa precios persistidos en SQLite, no cálculos improvisados en frontend. Esto permite reproducibilidad, automatización y trazabilidad.
