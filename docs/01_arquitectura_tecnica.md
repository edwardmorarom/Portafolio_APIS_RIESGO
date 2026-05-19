# Documentación técnica del Proyecto Portafolio Riesgo USTA

**Versión documental:** 2026-05-18  
**Repositorio:** `portafolio-riesgo`  
**Rama de trabajo:** `backend`  
**Ubicación recomendada dentro del repo:** `docs/01_arquitectura_tecnica.md`

---

## 1. Propósito del documento

Este documento describe la arquitectura técnica actual del proyecto **Portafolio Riesgo USTA**.

Su objetivo es dejar documentado:

- La estructura general del repositorio.
- La separación backend/frontend.
- Las capas internas del backend.
- Los routers FastAPI existentes.
- Los servicios de negocio.
- Los schemas Pydantic y validadores.
- Los decoradores utilizados.
- Las dependencias con `Depends`.
- La persistencia con SQLAlchemy y SQLite.
- El flujo de activos, precios, Perri y dashboard.
- Los jobs automáticos.
- Los tests.
- Los workflows de GitHub Actions.
- La configuración Docker.
- Lo implementado y lo pendiente.

---

## 2. Arquitectura general

El proyecto mantiene una separación clara entre backend y frontend:

```text
portafolio-riesgo/
├── backend/
│   ├── app/
│   │   ├── api/
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
├── requirements.txt
├── roboadvisor_cache.csv
└── README.md
```

Regla de diseño:

```text
Frontend consume el backend.
Backend calcula, valida, persiste y expone datos.
Frontend visualiza, filtra e interpreta.
```

---

## 3. Capas del backend

### 3.1 Entrada principal

Archivo:

```text
backend/app/main.py
```

Responsabilidades:

- Crear la aplicación FastAPI.
- Configurar CORS.
- Inicializar SQLite mediante `lifespan`.
- Registrar manejador de excepciones.
- Exponer `/` y `/health`.
- Montar `api_router` con el prefijo configurado.

Decoradores relevantes:

```python
@asynccontextmanager
@app.exception_handler(AppBaseException)
@app.get("/", tags=["Root"])
@app.get("/health", tags=["Health"])
```

Flujo de arranque:

```text
uvicorn app.main:app
        ↓
lifespan(app)
        ↓
init_db()
        ↓
Base.metadata.create_all()
        ↓
api_router disponible
```

---

### 3.2 API / routers

Ubicación:

```text
backend/app/api/
backend/app/api/v1/
```

Responsabilidades:

- Recibir solicitudes HTTP.
- Definir endpoints.
- Inyectar servicios con `Depends`.
- Delegar la lógica a la capa `services`.
- Devolver respuestas validadas por schemas.

Router central:

```text
backend/app/api/router.py
```

Routers registrados actualmente:

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

### 3.3 Schemas

Ubicación:

```text
backend/app/schemas/
```

Responsabilidades:

- Definir contratos de entrada y salida.
- Validar tickers, fechas, pesos, perfiles, distribuciones y modos.
- Documentar campos para Swagger/OpenAPI.
- Evitar que reglas de validación queden dispersas en servicios o frontend.

Decoradores principales:

```python
@field_validator(...)
@model_validator(...)
```

---

### 3.4 Servicios

Ubicación:

```text
backend/app/services/
```

Responsabilidades:

- Ejecutar lógica financiera, estadística y de riesgo.
- Construir matrices de retornos.
- Calcular indicadores, CAPM, VaR, CVaR, GARCH, Markowitz y señales.
- Leer datos desde SQLite o clientes externos.
- Mantener routers delgados.

Regla de diseño:

```text
Router recibe.
Schema valida.
Service calcula.
Client descarga.
DB persiste.
Frontend visualiza.
```

---

### 3.5 Clientes externos

Ubicación:

```text
backend/app/clients/
```

Clientes actuales:

```text
MarketClient
MacroClient
```

`MarketClient` se usa para:

- Descargar precios desde yfinance.
- Convertir OHLC a USD.
- Aplicar metadata de moneda y escala.
- Validar rangos de fechas.

`MacroClient` se usa para:

- Consultar tasa libre de riesgo.
- Consultar inflación si existe `FRED_API_KEY`.
- Construir snapshot macroeconómico.

---

### 3.6 Core

Ubicación:

```text
backend/app/core/
```

Contiene piezas transversales:

```text
settings.py
dependencies.py
decorators.py
exceptions.py
error_catalog.py
security.py
assets_registry.py
market_utils.py
help_catalog.py
```

---

### 3.7 Base de datos

Ubicación:

```text
backend/app/db/
```

Componentes:

```text
database.py
models.py
seed_db.py
import_perri_prices.py
build_perri_universe.py
```

Responsabilidades:

- Configurar SQLAlchemy.
- Crear sesión por request.
- Inicializar tablas.
- Sembrar activos.
- Importar precios históricos.
- Construir universo institucional de Perri.

---

### 3.8 Jobs

Ubicación:

```text
backend/app/jobs/
```

Job actual:

```text
run_perri_optimization.py
```

Responsabilidades:

- Ejecutar optimización institucional de Perri.
- Guardar resultado en JSON.
- Preparar el flujo para GitHub Actions.

---

## 4. Dependencias e inyección con FastAPI

Archivo principal:

```text
backend/app/core/dependencies.py
```

Este archivo define cómo se construyen clientes y servicios.

Flujo típico:

```text
Endpoint FastAPI
    ↓ Depends(get_market_service)
MarketService
    ↓ Depends(get_market_client)
MarketClient
    ↓ Depends(get_app_settings)
Settings
```

Dependencias principales:

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

La dependencia de base de datos es:

```python
db: Session = Depends(get_db)
```

Se usa en módulos como:

```text
assets
market
perri
persistence
```

---

## 5. Configuración

Archivo:

```text
backend/app/core/settings.py
```

Clase principal:

```python
class Settings(BaseSettings)
```

Campos relevantes:

```text
APP_NAME
APP_VERSION
APP_ENV
DEBUG
API_V1_PREFIX
DATABASE_URL
DEFAULT_START_DATE
DEFAULT_END_DATE
GLOBAL_BENCHMARK
DEFAULT_BASE_CURRENCY
RF_TICKER_USD
RF_TICKER_EUR
RF_TICKER_COP_PROXY
FRED_API_KEY
ALLOWED_ORIGINS
MIN_OBS_VAR
MIN_OBS_CAPM
MIN_OBS_PORTFOLIO
```

`get_settings()` usa `@lru_cache`, por lo tanto la configuración se reutiliza y no se recalcula en cada request.

---

## 6. Persistencia con SQLAlchemy y SQLite

### 6.1 database.py

Archivo:

```text
backend/app/db/database.py
```

Responsabilidades:

- Definir `Base`.
- Resolver ruta estable de SQLite.
- Crear `engine`.
- Crear `SessionLocal`.
- Exponer `get_db`.
- Exponer `init_db`.

La base correcta debe resolverse a:

```text
backend/data/portafolio_riesgo.db
```

Esto evita crear accidentalmente una base vacía en:

```text
data/portafolio_riesgo.db
```

cuando se ejecutan comandos desde la raíz.

---

### 6.2 models.py

Modelos actuales:

```python
Asset
Price
Portfolio
PredictionLog
```

Relación principal:

```text
Asset 1 ─── N Price
```

Tabla `assets`:

- Guarda ticker.
- Nombre.
- País.
- Clase de activo.
- Moneda.
- Benchmark recomendado.
- Fuente.
- Bandera `include_in_perri`.

Tabla `prices`:

- Guarda cierres históricos.
- Cierre original.
- Moneda original.
- FX ticker.
- FX rate a USD.
- Cierre convertido a USD.
- Fuente.

Campos relevantes de precios:

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

### 6.3 seed_db.py

Responsabilidades:

- Insertar activos base del proyecto.
- Insertar universo Perri.
- Actualizar metadata si el activo ya existe.
- Mantener SQLite sincronizada con `perri_universe.json`.

---

### 6.4 import_perri_prices.py

Responsabilidades:

- Leer `roboadvisor_cache.csv`.
- Insertar cierres históricos en SQLite.
- Evitar duplicados.
- Guardar `close_original` y `close_usd`.
- Asumir `fx_rate_to_usd = 1.0` para activos actualmente clasificados en USD.

---

## 7. Decoradores

### 7.1 Decoradores FastAPI

Se usan en routers y `main.py`:

```python
@router.get(...)
@router.post(...)
@app.get(...)
@app.exception_handler(...)
```

Ejemplos:

```python
@router.get("/prices/{ticker}", response_model=PricesResponse)
@router.post("/var", response_model=PortfolioVarResponse)
@router.get("/latest", summary="Última optimización precalculada de Perri")
```

### 7.2 Decoradores Pydantic

Se usan en schemas:

```python
@field_validator(...)
@model_validator(...)
```

Objetivo:

- Normalizar tickers.
- Validar pesos.
- Validar perfiles.
- Validar tipos de retorno.
- Validar distribuciones.
- Mapear alias del frontend.

### 7.3 Decorador propio

Archivo:

```text
backend/app/core/decorators.py
```

Decorador:

```python
log_execution_time(func)
```

Uso:

```text
Medir tiempo de ejecución de funciones sensibles, especialmente descargas de mercado.
```

---

## 8. Routers y módulos API

### 8.1 assets

Archivo:

```text
backend/app/api/v1/assets.py
```

Endpoints:

```text
GET /api/v1/assets/
GET /api/v1/assets/search
GET /api/v1/assets/summary
```

Servicio:

```text
AssetsService
```

Schemas:

```text
AssetUniverseItem
AssetUniverseResponse
AssetSearchResponse
```

Dependencias:

```python
service: AssetsService = Depends(get_assets_service)
db: Session = Depends(get_db)
```

Responsabilidad:

- Listar universo de activos.
- Buscar activos.
- Mostrar metadata metodológica de Perri.
- Resumir activos por clase y benchmark.

---

### 8.2 market

Archivo:

```text
backend/app/api/v1/market.py
```

Endpoints:

```text
GET /api/v1/market/prices/{ticker}
GET /api/v1/market/returns/{ticker}
```

Servicio:

```text
MarketService
```

Schemas:

```text
PricePoint
PricesResponse
ReturnPoint
ReturnsResponse
```

Dependencias:

```python
service: MarketService = Depends(get_market_service)
db: Session = Depends(get_db)
```

Responsabilidad:

- Consultar precios históricos.
- Consultar rendimientos.
- Leer primero desde SQLite.
- Usar `MarketClient` como respaldo.

---

### 8.3 technical

Archivo:

```text
backend/app/api/v1/technical.py
```

Endpoint:

```text
GET /api/v1/technical/indicators/{ticker}
```

Servicio:

```text
TechnicalService
```

Responsabilidad:

- Calcular indicadores técnicos:
  - SMA
  - EMA
  - RSI
  - Bollinger
  - MACD
  - Estocástico

---

### 8.4 returns-stats

Archivo:

```text
backend/app/api/v1/returns_stats.py
```

Endpoint:

```text
GET /api/v1/returns-stats/summary/{ticker}
```

Servicio:

```text
ReturnsStatsService
```

Responsabilidad:

- Calcular estadísticas descriptivas.
- Pruebas de normalidad.
- Histograma.
- Boxplot.
- Q-Q plot.

Validadores relacionados:

```text
ticker
return_type
mode
```

---

### 8.5 garch

Archivo:

```text
backend/app/api/v1/garch.py
```

Endpoint:

```text
GET /api/v1/garch/{ticker}
```

Servicio:

```text
GarchService
```

Responsabilidad:

- Ajustar ARCH.
- Ajustar GARCH.
- Ajustar EGARCH.
- Comparar AIC/BIC.
- Diagnosticar residuos.
- Pronosticar volatilidad.

Validadores relacionados:

```text
ticker
return_type
mode
distribution
```

---

### 8.6 capm

Archivo:

```text
backend/app/api/v1/capm.py
```

Endpoints:

```text
GET /api/v1/capm/{ticker}
POST /api/v1/capm/portfolio
```

Servicio:

```text
CapmService
```

Dependencia de seguridad en endpoint de portafolio:

```python
_: None = Depends(require_internal_api_key)
```

Responsabilidad:

- Calcular beta.
- Calcular alpha.
- Calcular R².
- Calcular retorno esperado CAPM.
- Calcular CAPM de portafolio.

Validadores relacionados:

```text
tickers
weights
base_currency
return_type
```

---

### 8.7 risk

Archivo:

```text
backend/app/api/v1/risk.py
```

Endpoint:

```text
POST /api/v1/risk/var
```

Servicio:

```text
RiskService
```

Seguridad:

```python
_: None = Depends(require_internal_api_key)
```

Responsabilidad:

- VaR histórico.
- VaR paramétrico.
- VaR Monte Carlo.
- CVaR histórico.
- CVaR paramétrico.
- CVaR Monte Carlo.
- Test de Kupiec.

Validadores relacionados:

```text
weights
tickers
return_type
distribution
```

---

### 8.8 portfolio

Archivo:

```text
backend/app/api/v1/portfolio.py
```

Endpoint:

```text
POST /api/v1/portfolio/efficient-frontier
```

Servicio:

```text
PortfolioService
```

Responsabilidad:

- Frontera eficiente.
- Portafolio de mínima varianza.
- Portafolio de máximo Sharpe.
- Top portafolios.
- Matriz de correlación.
- Portafolio objetivo.
- Portafolio sugerido por perfil.

Validadores relacionados:

```text
tickers
return_type
risk_profile
target_return_annual
rf_annual
```

---

### 8.9 benchmark

Archivo:

```text
backend/app/api/v1/benchmark.py
```

Endpoint:

```text
POST /api/v1/benchmark/compare
```

Servicio:

```text
BenchmarkService
```

Responsabilidad:

- Comparar portafolio contra benchmark.
- Calcular tracking error.
- Information Ratio.
- Sharpe.
- Alpha.
- Drawdown.

Validadores relacionados:

```text
tickers
weights
base_currency
return_type
mode
```

---

### 8.10 macro

Archivo:

```text
backend/app/api/v1/macro.py
```

Endpoints:

```text
GET /api/v1/macro/
GET /api/v1/macro/fx-spot/{base_currency}
```

Servicio:

```text
MacroService
```

Responsabilidad:

- Snapshot macroeconómico.
- Tasa libre de riesgo.
- Inflación si existe FRED.
- Spot FX.

---

### 8.11 decision

Archivo:

```text
backend/app/api/v1/decision.py
```

Endpoint:

```text
POST /api/v1/decision/panel
```

Servicio:

```text
DecisionService
```

Depende de:

```text
RiskService
PortfolioService
CapmService
```

Responsabilidad:

- Integrar señales de riesgo, portafolio y CAPM.
- Emitir postura de decisión.

---

### 8.12 investor

Archivo:

```text
backend/app/api/v1/investor.py
```

Endpoint:

```text
POST /api/v1/investor/preferences
```

Servicio:

```text
InvestorService
```

Responsabilidad:

- Validar preferencias del inversionista.
- Determinar perfil de riesgo.
- Resolver horizonte.

Validadores:

```text
tickers
weights_pct
base_currency
risk_profile
horizon_type
return_type
mode
validaciones cruzadas
```

---

### 8.13 alerts

Archivo:

```text
backend/app/api/v1/alerts.py
```

Endpoint:

```text
GET /api/v1/alerts/{ticker}
```

Servicio:

```text
AlertsService
```

Responsabilidad:

- Generar señales técnicas de compra, venta o neutralidad.

---

### 8.14 valuation

Archivo:

```text
backend/app/api/v1/valuation.py
```

Endpoints:

```text
POST /api/v1/valuation/nelson-siegel
POST /api/v1/valuation/black-scholes
```

Servicios:

```text
YieldService
OptionService
```

Responsabilidad:

- Ajustar curva Nelson-Siegel.
- Valorar opciones Black-Scholes.
- Calcular griegas.

---

### 8.15 roboadvisor

Archivo:

```text
backend/app/api/v1/roboadvisor.py
```

Endpoint:

```text
POST /api/v1/roboadvisor/suggest
```

Servicio:

```text
RoboAdvisorService
```

Responsabilidad:

- Mezclar activos sugeridos con activos personalizados.
- Usar `roboadvisor_cache.csv`.
- Optimizar vía `PortfolioOptimizerSingleton`.

Nota técnica:

```text
RoboAdvisor actual se mantiene separado de Perri institucional.
```

---

### 8.16 perri

Archivo:

```text
backend/app/api/v1/perri.py
```

Endpoints:

```text
GET /api/v1/perri/latest
GET /api/v1/perri/optimize
```

Servicio:

```text
PerriOptimizerService
```

Responsabilidad:

- `/latest`: devolver JSON precalculado.
- `/optimize`: recalcular optimización desde SQLite.
- Exponer portafolios institucionales exactos por horizonte, tamaño y objetivo.

Dependencia:

```python
db: Session = Depends(get_db)
```

---

### 8.17 persistence

Archivo:

```text
backend/app/api/v1/persistence.py
```

Endpoint:

```text
GET /api/v1/persistence/health
```

Responsabilidad:

- Validar conexión SQLite.
- Contar tablas principales:
  - assets
  - prices
  - portfolios
  - predictions_log

---

## 9. Perri institucional

Perri es la capa institucional del proyecto para optimización automática desde datos persistidos.

### 9.1 Archivos principales

```text
backend/app/db/build_perri_universe.py
backend/app/db/seed_db.py
backend/app/db/import_perri_prices.py
backend/app/services/perri_optimizer_service.py
backend/app/api/v1/perri.py
backend/app/jobs/run_perri_optimization.py
backend/data/perri_universe.json
backend/data/perri_latest_optimization.json
```

### 9.2 Flujo de universo

```text
roboadvisor_cache.csv
        ↓
build_perri_universe.py
        ↓
backend/data/perri_universe.json
        ↓
seed_db.py
        ↓
tabla assets
```

Clasificación de activos:

```text
renta_variable
renta_fija
commodity
etf_global
etf_sectorial
efectivo_o_corto_plazo
```

Metadata de Perri:

```text
tipo_activo / asset_type
moneda_origen / currency
fx_ticker
benchmark_ticker
benchmark_description
include_in_perri
source
```

---

### 9.3 Flujo de precios

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

---

### 9.4 Flujo de optimización

```text
assets + prices en SQLite
        ↓
PerriOptimizerService
        ↓
run_optimization()
        ↓
/api/v1/perri/optimize
```

El servicio calcula portafolios institucionales exactos para:

Objetivos:

- Portafolio de mínimo riesgo (`min_risk`).
- Portafolio de máximo Sharpe (`max_sharpe`).
- Portafolio de máxima rentabilidad (`max_return`).

Tamaños exactos:

- 5 activos.
- 10 activos.
- 15 activos.

Horizontes:

- 1 año (`1y`).
- 3 años (`3y`).
- 5 años (`5y`).

Universo usado actualmente:

```text
renta_variable
renta_fija
```

---

### 9.5 Flujo de JSON precalculado

```text
PerriOptimizerService
        ↓
run_perri_optimization.py
        ↓
backend/data/perri_latest_optimization.json
        ↓
/api/v1/perri/latest
        ↓
frontend futuro / dashboard Perri
```

Esto evita recalcular Markowitz en cada consulta del dashboard.

---

## 10. Frontend Streamlit

Ubicación:

```text
frontend/
```

Componentes:

```text
frontend/app.py
frontend/config.py
frontend/pages/
frontend/services/api_client.py
frontend/ui/
```

### 10.1 app.py

Responsabilidad:

- Entrada principal del dashboard.
- Login básico.
- Navegación de páginas.

### 10.2 api_client.py

Responsabilidad:

- Centralizar llamadas HTTP.
- Manejar errores.
- Construir URLs.
- Enviar API key interna cuando aplique.

Métodos relevantes:

```text
get_assets()
search_assets()
get_help_catalog()
get_prices()
get_returns()
get_technical_indicators()
get_returns_stats()
get_alerts()
get_garch()
get_capm()
get_portfolio_capm()
post_var_risk()
post_efficient_frontier()
get_macro_snapshot()
post_benchmark_compare()
get_decision_panel()
validate_investor_preferences()
get_perri_latest()
post_roboadvisor_suggest()
```

### 10.3 ui/

Componentes reutilizables:

```text
cards.py
dashboard_ui.py
page_setup.py
plot_style.py
theme.py
```

Responsabilidades:

- Tarjetas.
- Chips.
- Layout.
- Estilos globales.
- Tema visual.
- Gráficas Plotly.
- Encabezados.
- Tooltips.

### 10.4 pages/

Páginas actuales:

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

---

## 11. Módulos frontend y dependencia con backend

### 11.1 Contextualización

Consume:

```text
/api/v1/assets/
/api/v1/assets/search
/api/v1/help/catalog
```

Muestra activos base, activos ampliados, metadata de Perri, clase de activo, benchmark metodológico, fuente y resumen de universo.

### 11.2 Técnico

Consume:

```text
/api/v1/technical/indicators/{ticker}
/api/v1/market/prices/{ticker}
```

Muestra precio, SMA, EMA, RSI, Bollinger, MACD y estocástico.

### 11.3 Rendimientos

Consume:

```text
/api/v1/returns-stats/summary/{ticker}
/api/v1/market/returns/{ticker}
```

Muestra rendimientos, estadísticas, histograma, boxplot, Q-Q plot y pruebas de normalidad.

### 11.4 GARCH

Consume:

```text
/api/v1/garch/{ticker}
```

Muestra ARCH, GARCH, EGARCH, comparación de modelos, volatilidad condicional y pronóstico.

### 11.5 CAPM

Consume:

```text
/api/v1/capm/{ticker}
/api/v1/capm/portfolio
```

Muestra beta, alpha, R², CAPM por activo y CAPM por portafolio.

### 11.6 VaR y CVaR

Consume:

```text
/api/v1/risk/var
```

Muestra VaR, CVaR, métodos histórico, paramétrico y Monte Carlo, riesgo monetario y Kupiec.

### 11.7 Markowitz

Consume:

```text
/api/v1/portfolio/efficient-frontier
```

Muestra frontera eficiente, mínima varianza, máximo Sharpe, matriz de correlación, perfil sugerido y portafolios top.

### 11.8 Señales

Consume:

```text
/api/v1/alerts/{ticker}
```

Muestra señales técnicas de compra, venta o neutralidad.

### 11.9 Macro y Benchmark

Consume:

```text
/api/v1/macro/
/api/v1/macro/fx-spot/{base_currency}
/api/v1/benchmark/compare
```

Muestra tasa libre de riesgo, inflación si existe FRED, FX spot, benchmark ACWI, alpha, tracking error e information ratio.

---

## 12. Tests

Ubicación:

```text
tests/
```

Tests actuales:

```text
tests/test_perri_latest.py
tests/test_perri_optimize.py
tests/test_perri_horizons.py
```

### 12.1 test_perri_latest.py

Valida:

```text
GET /api/v1/perri/latest
```

Comprueba:

- HTTP 200.
- Job correcto.
- JSON con `result`.
- `status = ok`.
- Activos elegibles.
- Pesos de mínimo riesgo.
- Pesos de máximo Sharpe.
- Pesos de máxima rentabilidad.
- Volatilidades no negativas.

---

### 12.2 test_perri_optimize.py

Valida:

```text
GET /api/v1/perri/optimize
```

Comprueba:

- HTTP 200.
- `history_years = 5`.
- `rf_annual = 0.04`.
- Existe `min_risk`.
- Existe `max_sharpe`.
- Existe `max_return`.
- Objetivos correctos.
- Suma de pesos cercana a 1.

---

### 12.3 test_perri_horizons.py

Valida:

```text
GET /api/v1/perri/latest
```

Comprueba que el JSON precalculado de Perri contenga:

- Horizontes exactos: `1y`, `3y`, `5y`.
- Tamaños exactos de portafolio: `5`, `10`, `15`.
- Objetivos exactos: `min_risk`, `max_sharpe`, `max_return`.
- Modo de selección `exact`.
- Cantidad de activos seleccionados igual al tamaño solicitado.

Los tests usan:

```python
with TestClient(app) as client:
```

Esto activa correctamente el `lifespan` de FastAPI.

---

## 13. GitHub Actions

Ubicación:

```text
.github/workflows/
```

Workflows actuales:

```text
backend-ci.yml
perri-scheduled-update.yml
```

### 13.1 Backend CI

Responsabilidad:

- Instalar dependencias.
- Compilar backend.
- Preparar base SQLite.
- Ejecutar tests de Perri.

Flujo:

```text
checkout
    ↓
setup-python 3.11
    ↓
pip install -r backend/requirements.txt
    ↓
python -m compileall backend/app
    ↓
seed_db
    ↓
import_perri_prices
    ↓
run_perri_optimization
    ↓
pytest
```

---

### 13.2 Actualización automática Perri

Responsabilidad:

- Ejecutar dos veces al día.
- Cargar históricos.
- Optimizar Perri.
- Guardar JSON actualizado.
- Publicar cambios en rama `backend`.

Horarios:

```text
09:30 UTC = 04:30 Colombia
22:30 UTC = 17:30 Colombia
```

---

## 14. Docker

Archivos:

```text
backend/Dockerfile
docker-compose.yml
.dockerignore
```

### 14.1 Dockerfile

Responsabilidad:

- Usar `python:3.11-slim`.
- Instalar dependencias.
- Copiar backend.
- Copiar `roboadvisor_cache.csv`.
- Exponer puerto 8000.
- Ejecutar Uvicorn.

Comando final:

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 14.2 docker-compose.yml

Servicio:

```text
backend
```

Variables:

```text
APP_ENV=docker
DEBUG=false
DATABASE_URL=sqlite:///./data/portafolio_riesgo.db
ALLOWED_ORIGINS=http://localhost:8501,http://127.0.0.1:8501
```

Puerto:

```text
8000:8000
```

### 14.3 .dockerignore

Evita enviar al contexto Docker:

```text
.git
.github
.venv
.pytest_cache
__pycache__
.env
data/*.db
backend/data/*.db
*.sqlite
*.sqlite3
```

Estado actual:

```text
Build Docker validado correctamente.
Falta validar docker compose up + /health.
```

---

## 15. Relación entre documentos y módulos

### 15.1 README.md

Debe servir como guía principal para:

- Qué es el proyecto.
- Cómo instalar.
- Cómo ejecutar.
- Qué módulos tiene.
- Qué endpoints principales existen.
- Qué comandos usar.

### 15.2 docs/00_snapshot_codigo_actual.md

Debe servir como evidencia del estado real del código.

Uso:

```text
Auditoría técnica rápida.
Base para documentación.
Referencia para no inventar archivos o funciones.
```

### 15.3 docs/01_arquitectura_tecnica.md

Este documento debe servir como explicación técnica profunda.

Uso:

```text
Arquitectura.
Capas.
Módulos.
Decoradores.
Dependencias.
Validadores.
Flujos de datos.
CI/CD.
Docker.
Perri.
```

### 15.4 Swagger/OpenAPI

Swagger sigue siendo la documentación interactiva de la API:

```text
http://127.0.0.1:8000/docs
```

Relación correcta:

```text
README.md → guía general
docs/00_snapshot_codigo_actual.md → evidencia automática
docs/01_arquitectura_tecnica.md → arquitectura explicada
Swagger → contrato interactivo de endpoints
Código → fuente de verdad final
```

---

## 16. Estado de cumplimiento técnico

### Implementado

```text
FastAPI
Pydantic
Pydantic Settings
SQLAlchemy
SQLite
Persistencia de activos
Persistencia de precios
Lectura de precios desde SQLite
Conversión metodológica a USD
Nelson-Siegel
Black-Scholes
CAPM
VaR/CVaR
Markowitz
GARCH
RoboAdvisor
Perri institucional con 1y, 3y, 5y
Perri institucional con 5, 10 y 15 activos exactos
Perri institucional con min_risk, max_sharpe y max_return
KYC / preferencias de inversionista
Login básico en frontend
Dashboard Streamlit
Tests con pytest
TestClient
GitHub Actions CI
GitHub Actions programado
Dockerfile
docker-compose
```

### Parcial o pendiente

```text
ML Singleton predictivo real con endpoint /predict
Admin dashboard robusto
Roles robustos
Reportes PDF
Deploy PaaS final
Más tests por módulo
Healthcheck Docker validado
Frontend específico para Perri latest
```

---

## 17. Comandos operativos

### 17.1 Backend local

```powershell
cd C:\Users\edwar\Desktop\portafolio-riesgo\backend
uvicorn app.main:app --reload
```

### 17.2 Frontend

```powershell
cd C:\Users\edwar\Desktop\portafolio-riesgo
streamlit run frontend/app.py
```

### 17.3 Cargar datos Perri

```powershell
cd C:\Users\edwar\Desktop\portafolio-riesgo\backend
python -m app.db.seed_db
python -m app.db.import_perri_prices
python -m app.jobs.run_perri_optimization
```

### 17.4 Tests

```powershell
cd C:\Users\edwar\Desktop\portafolio-riesgo
python -m pytest tests\test_perri_latest.py tests\test_perri_optimize.py tests\test_perri_horizons.py -q
```

### 17.5 Docker

```powershell
cd C:\Users\edwar\Desktop\portafolio-riesgo
docker compose build backend
docker compose up backend
```

### 17.6 Validar API

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/health"
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/v1/perri/latest"
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/v1/perri/optimize?history_years=5&rf_annual=0.04"
```

---

## 18. Reglas de mantenimiento

1. Revisar el código real antes de modificar.
2. No duplicar endpoints existentes.
3. Mantener routers delgados.
4. Mantener lógica en services.
5. Mantener validaciones en schemas.
6. Usar `Depends` para dependencias.
7. Usar SQLAlchemy para persistencia.
8. No versionar bases `.db`.
9. Ejecutar `compileall` antes de commit.
10. Ejecutar tests antes de commit.
11. Hacer commits pequeños y explicativos.
12. Documentar cada cambio relevante.
13. Actualizar README cuando cambien instalación, ejecución o arquitectura.
14. Actualizar docs cuando cambien flujos técnicos.

---

## 19. Próximos pasos recomendados

1. Validar `docker compose up backend` y `/health`.
2. Guardar archivos Docker en Git.
3. Integrar en backend la comparación de Markowitz contra umbrales Perri exactos.
4. Diseñar backend del chatbot experto.
5. Crear frontend específico para `/api/v1/perri/latest` al final.
6. Ampliar tests a `market`, `assets` y `persistence`.
7. Revisar `GitHub Actions` en la pestaña Actions.
8. Crear reportes PDF.
9. Diseñar admin dashboard.
10. Fortalecer login y roles.
11. Implementar ML Singleton predictivo real.
