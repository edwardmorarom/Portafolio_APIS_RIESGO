        # Snapshot técnico actual del Proyecto Portafolio Riesgo USTA

        Generado: 2026-05-18T20:19:23

        ## Git

        ```text
        On branch backend
        Your branch is up to date with 'origin/backend'.

        nothing to commit, working tree clean
        ```

        ## Estructura detectada

        ```text
        .devcontainer/devcontainer.json
        .env.example
        .github/workflows/backend-ci.yml
        .github/workflows/perri-scheduled-update.yml
        .vscode/settings.json
        backend/app/__init__.py
        backend/app/api/__init__.py
        backend/app/api/router.py
        backend/app/api/v1/__init__.py
        backend/app/api/v1/alerts.py
        backend/app/api/v1/assets.py
        backend/app/api/v1/benchmark.py
        backend/app/api/v1/capm.py
        backend/app/api/v1/decision.py
        backend/app/api/v1/garch.py
        backend/app/api/v1/help.py
        backend/app/api/v1/investor.py
        backend/app/api/v1/macro.py
        backend/app/api/v1/market.py
        backend/app/api/v1/perri.py
        backend/app/api/v1/persistence.py
        backend/app/api/v1/portfolio.py
        backend/app/api/v1/returns_stats.py
        backend/app/api/v1/risk.py
        backend/app/api/v1/roboadvisor.py
        backend/app/api/v1/technical.py
        backend/app/api/v1/valuation.py
        backend/app/clients/__init__.py
        backend/app/clients/macro_client.py
        backend/app/clients/market_client.py
        backend/app/core/__init__.py
        backend/app/core/assets_registry.py
        backend/app/core/decorators.py
        backend/app/core/dependencies.py
        backend/app/core/error_catalog.py
        backend/app/core/exceptions.py
        backend/app/core/help_catalog.py
        backend/app/core/market_utils.py
        backend/app/core/security.py
        backend/app/core/settings.py
        backend/app/db/__init__.py
        backend/app/db/build_perri_universe.py
        backend/app/db/database.py
        backend/app/db/import_perri_prices.py
        backend/app/db/models.py
        backend/app/db/seed_db.py
        backend/app/domain/__init__.py
        backend/app/jobs/__init__.py
        backend/app/jobs/run_perri_optimization.py
        backend/app/main.py
        backend/app/schemas/__init__.py
        backend/app/schemas/alerts.py
        backend/app/schemas/benchmark.py
        backend/app/schemas/capm.py
        backend/app/schemas/common.py
        backend/app/schemas/decision.py
        backend/app/schemas/error.py
        backend/app/schemas/garch.py
        backend/app/schemas/help.py
        backend/app/schemas/investor.py
        backend/app/schemas/macro.py
        backend/app/schemas/market.py
        backend/app/schemas/portfolio.py
        backend/app/schemas/returns_stats.py
        backend/app/schemas/risk.py
        backend/app/schemas/technical.py
        backend/app/schemas/valuation.py
        backend/app/services/__init__.py
        backend/app/services/alerts_service.py
        backend/app/services/assets_service.py
        backend/app/services/benchmark_service.py
        backend/app/services/capm_service.py
        backend/app/services/decision_service.py
        backend/app/services/garch_service.py
        backend/app/services/help_service.py
        backend/app/services/investor_service.py
        backend/app/services/macro_service.py
        backend/app/services/market_service.py
        backend/app/services/option_service.py
        backend/app/services/perri_optimizer_service.py
        backend/app/services/portfolio_service.py
        backend/app/services/returns_stats_service.py
        backend/app/services/risk_service.py
        backend/app/services/roboadvisor_service.py
        backend/app/services/technical_service.py
        backend/app/services/yield_service.py
        backend/data/perri_latest_optimization.json
        backend/data/perri_universe.json
        backend/data/users.json
        backend/requirements.txt
        backend/runtime.txt
        backend/update_cache.py
        docker-compose.yml
        docs/00_snapshot_codigo_actual.md
        docs/01_arquitectura_tecnica.md
        docs/generar_snapshot_codigo.py
        frontend/.streamlit/secrets.toml
        frontend/app.py
        frontend/config.py
        frontend/pages/01_Tecnico.py
        frontend/pages/02_Rendimientos.py
        frontend/pages/03_Garch.py
        frontend/pages/04_Capm.py
        frontend/pages/05_Var_Cvar.py
        frontend/pages/06_Markowitz.py
        frontend/pages/07_Señales.py
        frontend/pages/08_Macro_Benchmark.py
        frontend/pages/0_Contextualizacion.py
        frontend/services/api_client.py
        frontend/ui/__init__.py
        frontend/ui/cards.py
        frontend/ui/dashboard_filters.py
        frontend/ui/dashboard_ui.py
        frontend/ui/page_setup.py
        frontend/ui/plot_style.py
        frontend/ui/theme.py
        README.md
        requirements.txt
        tests/test_perri_horizons.py
        tests/test_perri_latest.py
        tests/test_perri_optimize.py
        ```

        ## README actual

        ```markdown
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

        ```

        ## Archivos Python analizados

        ### `backend/app/__init__.py`

        ### `backend/app/api/__init__.py`

        ### `backend/app/api/router.py`

        **Imports internos:**

        - `from app.api.v1 import alerts, assets, benchmark, capm, decision, garch, help, investor, macro, market, persistence, portfolio, returns_stats, risk, technical, valuation, roboadvisor, perri`

        ### `backend/app/api/v1/__init__.py`

        ### `backend/app/api/v1/alerts.py`

        **Imports internos:**

        - `from app.core.dependencies import get_alerts_service`
        - `from app.schemas.alerts import AlertsResponse`
        - `from app.services.alerts_service import AlertsService`

        **Decoradores detectados:**

        - `@router.get("/{ticker}", summary="Alertas tecnicas por activo", response_model=AlertsResponse)`

        **Clases y funciones:**

        - `async def get_alerts(`

        **Dependencias / inyección detectada:**

        - `from app.core.dependencies import get_alerts_service`
        - `service: AlertsService = Depends(get_alerts_service),`

        ### `backend/app/api/v1/assets.py`

        **Imports internos:**

        - `from app.core.assets_registry import ALL_ASSETS, MAX_ASSETS_ALLOWED`
        - `from app.core.dependencies import get_assets_service, get_db`
        - `from app.core.settings import get_settings`
        - `from app.schemas.common import AssetSearchResponse, AssetUniverseItem, AssetUniverseResponse`
        - `from app.services.assets_service import AssetsService`

        **Decoradores detectados:**

        - `@router.get("/", summary="Listar universo de activos", response_model=AssetUniverseResponse)`
        - `@router.get("/search", summary="Buscar activos por nombre o ticker", response_model=AssetSearchResponse)`
        - `@router.get("/summary", summary="Resumen metodológico del universo de activos")`

        **Clases y funciones:**

        - `async def list_assets(`
        - `async def search_assets(`
        - `async def summarize_assets(`

        **Dependencias / inyección detectada:**

        - `from app.core.dependencies import get_assets_service, get_db`
        - `service: AssetsService = Depends(get_assets_service),`
        - `db: Session = Depends(get_db),`
        - `service: AssetsService = Depends(get_assets_service),`
        - `db: Session = Depends(get_db),`
        - `service: AssetsService = Depends(get_assets_service),`
        - `db: Session = Depends(get_db),`

        ### `backend/app/api/v1/benchmark.py`

        **Imports internos:**

        - `from app.core.dependencies import get_benchmark_service`
        - `from app.core.security import require_internal_api_key`
        - `from app.schemas.benchmark import BenchmarkCompareRequest, BenchmarkCompareResponse`
        - `from app.services.benchmark_service import BenchmarkService`

        **Decoradores detectados:**

        - `@router.post("/compare", summary="Comparar portafolio contra benchmark", response_model=BenchmarkCompareResponse)`

        **Clases y funciones:**

        - `async def compare_benchmark(`

        **Dependencias / inyección detectada:**

        - `from app.core.dependencies import get_benchmark_service`
        - `_: None = Depends(require_internal_api_key),`
        - `service: BenchmarkService = Depends(get_benchmark_service),`

        ### `backend/app/api/v1/capm.py`

        **Imports internos:**

        - `from app.core.dependencies import get_capm_service`
        - `from app.core.settings import get_settings`
        - `from app.schemas.capm import CapmResponse, PortfolioCapmRequest, PortfolioCapmResponse`
        - `from app.services.capm_service import CapmService`
        - `from app.core.security import require_internal_api_key`

        **Decoradores detectados:**

        - `@router.get("/{ticker}", summary="Calcular CAPM por activo", response_model=CapmResponse)`
        - `@router.post("/portfolio", summary="Calcular CAPM del portafolio", response_model=PortfolioCapmResponse)`

        **Clases y funciones:**

        - `async def get_capm(`
        - `async def get_portfolio_capm(`

        **Dependencias / inyección detectada:**

        - `from app.core.dependencies import get_capm_service`
        - `service: CapmService = Depends(get_capm_service),`
        - `_: None = Depends(require_internal_api_key),`
        - `service: CapmService = Depends(get_capm_service),`

        ### `backend/app/api/v1/decision.py`

        **Imports internos:**

        - `from app.core.dependencies import get_decision_service`
        - `from app.schemas.decision import DecisionPanelRequest, DecisionPanelResponse`
        - `from app.services.decision_service import DecisionService`
        - `from app.core.security import require_internal_api_key`

        **Decoradores detectados:**

        - `@router.post("/panel", summary="Panel integrador de decisión", response_model=DecisionPanelResponse)`

        **Clases y funciones:**

        - `async def decision_panel(`

        **Dependencias / inyección detectada:**

        - `from app.core.dependencies import get_decision_service`
        - `_: None = Depends(require_internal_api_key),`
        - `service: DecisionService = Depends(get_decision_service),`

        ### `backend/app/api/v1/garch.py`

        **Imports internos:**

        - `from app.core.dependencies import get_garch_service`
        - `from app.schemas.garch import GarchResponse`
        - `from app.services.garch_service import GarchService`

        **Decoradores detectados:**

        - `@router.get("/{ticker}", summary="Analisis ARCH GARCH EGARCH", response_model=GarchResponse)`

        **Clases y funciones:**

        - `async def get_garch_analysis(`

        **Dependencias / inyección detectada:**

        - `from app.core.dependencies import get_garch_service`
        - `service: GarchService = Depends(get_garch_service),`

        ### `backend/app/api/v1/help.py`

        **Imports internos:**

        - `from app.core.dependencies import get_help_service`
        - `from app.schemas.help import HelpCatalogResponse, HelpItem`
        - `from app.services.help_service import HelpService`

        **Decoradores detectados:**

        - `@router.get("/catalog", summary="Catalogo de ayudas para tooltips", response_model=HelpCatalogResponse)`

        **Clases y funciones:**

        - `async def get_help_catalog(`

        **Dependencias / inyección detectada:**

        - `from app.core.dependencies import get_help_service`
        - `service: HelpService = Depends(get_help_service),`

        ### `backend/app/api/v1/investor.py`

        **Imports internos:**

        - `from app.core.dependencies import get_investor_service`
        - `from app.schemas.investor import InvestorPreferencesRequest, InvestorPreferencesResponse`
        - `from app.services.investor_service import InvestorService`

        **Decoradores detectados:**

        - `@router.post("/preferences", summary="Validar preferencias del inversionista", response_model=InvestorPreferencesResponse)`

        **Clases y funciones:**

        - `async def validate_preferences(`

        **Dependencias / inyección detectada:**

        - `from app.core.dependencies import get_investor_service`
        - `service: InvestorService = Depends(get_investor_service),`

        ### `backend/app/api/v1/macro.py`

        **Imports internos:**

        - `from app.core.dependencies import get_macro_service`
        - `from app.schemas.macro import MacroSnapshotResponse`
        - `from app.services.macro_service import MacroService`
        - `from app.schemas.macro import FxSpotResponse`

        **Decoradores detectados:**

        - `@router.get("/", summary="Snapshot macroeconómico", response_model=MacroSnapshotResponse)`
        - `@router.get("/fx-spot/{base_currency}", summary="Spot FX y referencia macro por moneda base", response_model=FxSpotResponse)`

        **Clases y funciones:**

        - `async def get_macro_snapshot(`
        - `async def get_fx_spot(`

        **Dependencias / inyección detectada:**

        - `from app.core.dependencies import get_macro_service`
        - `service: MacroService = Depends(get_macro_service),`
        - `service: MacroService = Depends(get_macro_service),`

        ### `backend/app/api/v1/market.py`

        **Imports internos:**

        - `from app.core.dependencies import get_db, get_market_service`
        - `from app.schemas.market import PricePoint, PricesResponse, ReturnPoint, ReturnsResponse`
        - `from app.services.market_service import MarketService`

        **Decoradores detectados:**

        - `@router.get("/prices/{ticker}", summary="Precios históricos por ticker", response_model=PricesResponse)`
        - `@router.get("/returns/{ticker}", summary="Rendimientos por ticker", response_model=ReturnsResponse)`

        **Clases y funciones:**

        - `async def get_prices(`
        - `async def get_returns(`

        **Dependencias / inyección detectada:**

        - `from app.core.dependencies import get_db, get_market_service`
        - `service: MarketService = Depends(get_market_service),`
        - `db: Session = Depends(get_db),`
        - `service: MarketService = Depends(get_market_service),`
        - `db: Session = Depends(get_db),`

        ### `backend/app/api/v1/perri.py`

        **Imports internos:**

        - `from app.core.dependencies import get_db`
        - `from app.services.perri_optimizer_service import PerriOptimizerService`

        **Decoradores detectados:**

        - `@router.get("/latest", summary="Última optimización precalculada de Perri")`
        - `@router.get("/optimize", summary="Optimización institucional automática de Perri")`

        **Clases y funciones:**

        - `async def get_latest_perri_optimization() -> dict:`
        - `async def optimize_perri_portfolio(`

        **Dependencias / inyección detectada:**

        - `from app.core.dependencies import get_db`
        - `db: Session = Depends(get_db),`

        ### `backend/app/api/v1/persistence.py`

        **Imports internos:**

        - `from app.core.dependencies import get_db`
        - `from app.db.models import Asset, Portfolio, PredictionLog, Price`

        **Decoradores detectados:**

        - `@router.get("/health")`

        **Clases y funciones:**

        - `def persistence_health(db: Session = Depends(get_db)) -> dict:`

        **Dependencias / inyección detectada:**

        - `from app.core.dependencies import get_db`
        - `def persistence_health(db: Session = Depends(get_db)) -> dict:`

        ### `backend/app/api/v1/portfolio.py`

        **Imports internos:**

        - `from app.core.dependencies import get_portfolio_service`
        - `from app.schemas.portfolio import EfficientFrontierRequest, EfficientFrontierResponse`
        - `from app.services.portfolio_service import PortfolioService`
        - `from app.core.security import require_internal_api_key`

        **Decoradores detectados:**

        - `@router.post(`

        **Clases y funciones:**

        - `async def efficient_frontier(`

        **Dependencias / inyección detectada:**

        - `from app.core.dependencies import get_portfolio_service`
        - `_: None = Depends(require_internal_api_key),`
        - `service: PortfolioService = Depends(get_portfolio_service),`

        ### `backend/app/api/v1/returns_stats.py`

        **Imports internos:**

        - `from app.core.dependencies import get_returns_stats_service`
        - `from app.schemas.returns_stats import ReturnsStatsResponse`
        - `from app.services.returns_stats_service import ReturnsStatsService`

        **Decoradores detectados:**

        - `@router.get("/summary/{ticker}", summary="Estadistica de rendimientos", response_model=ReturnsStatsResponse)`

        **Clases y funciones:**

        - `async def get_returns_stats(`

        **Dependencias / inyección detectada:**

        - `from app.core.dependencies import get_returns_stats_service`
        - `service: ReturnsStatsService = Depends(get_returns_stats_service),`

        ### `backend/app/api/v1/risk.py`

        **Imports internos:**

        - `from app.core.dependencies import get_risk_service`
        - `from app.schemas.risk import PortfolioVarRequest, PortfolioVarResponse`
        - `from app.services.risk_service import RiskService`
        - `from app.core.security import require_internal_api_key`

        **Decoradores detectados:**

        - `@router.post("/var", summary="Calcular VaR y CVaR del portafolio", response_model=PortfolioVarResponse)`

        **Clases y funciones:**

        - `async def calculate_var(`

        **Dependencias / inyección detectada:**

        - `from app.core.dependencies import get_risk_service`
        - `_: None = Depends(require_internal_api_key),`
        - `service: RiskService = Depends(get_risk_service),`

        ### `backend/app/api/v1/roboadvisor.py`

        **Imports internos:**

        - `from app.clients.market_client import MarketClient`
        - `from app.core.dependencies import get_market_client`
        - `from app.services.roboadvisor_service import RoboAdvisorService`

        **Decoradores detectados:**

        - `@router.post("/suggest", summary="Generar Portafolio Híbrido Institucional")`

        **Clases y funciones:**

        - `class RoboAdvisorRequest(BaseModel):`
        - `def get_roboadvisor_service(market_client: MarketClient = Depends(get_market_client)) -> RoboAdvisorService:`
        - `async def suggest_portfolio(`

        **Dependencias / inyección detectada:**

        - `def get_roboadvisor_service(market_client: MarketClient = Depends(get_market_client)) -> RoboAdvisorService:`
        - `service: RoboAdvisorService = Depends(get_roboadvisor_service)`

        ### `backend/app/api/v1/technical.py`

        **Imports internos:**

        - `from app.core.dependencies import get_technical_service`
        - `from app.schemas.technical import TechnicalPoint, TechnicalResponse`
        - `from app.services.technical_service import TechnicalService`

        **Decoradores detectados:**

        - `@router.get("/indicators/{ticker}", summary="Indicadores técnicos por ticker", response_model=TechnicalResponse)`

        **Clases y funciones:**

        - `async def get_indicators(`

        **Dependencias / inyección detectada:**

        - `from app.core.dependencies import get_technical_service`
        - `service: TechnicalService = Depends(get_technical_service),`

        ### `backend/app/api/v1/valuation.py`

        **Imports internos:**

        - `from app.schemas.valuation import YieldCurveRequest, YieldCurveResponse, OptionValuationRequest, OptionValuationResponse`
        - `from app.services.yield_service import YieldService`
        - `from app.services.option_service import OptionService`

        **Decoradores detectados:**

        - `@router.post("/nelson-siegel", response_model=YieldCurveResponse, summary="Ajuste de curva Nelson-Siegel")`
        - `@router.post("/black-scholes", response_model=OptionValuationResponse, summary="Valoración de opciones Black-Scholes")`

        **Clases y funciones:**

        - `def get_yield_service() -> YieldService:`
        - `def get_option_service() -> OptionService:`
        - `async def fit_nelson_siegel(`
        - `async def calculate_option(`

        **Dependencias / inyección detectada:**

        - `def get_yield_service() -> YieldService:`
        - `def get_option_service() -> OptionService:`
        - `service: YieldService = Depends(get_yield_service)`
        - `service: OptionService = Depends(get_option_service)`

        ### `backend/app/clients/__init__.py`

        ### `backend/app/clients/macro_client.py`

        **Imports internos:**

        - `from app.core.settings import Settings`

        **Clases y funciones:**

        - `class MacroClient:`
        - `def __init__(self, settings: Settings) -> None:`
        - `def _get_last_close(self, ticker: str) -> float | None:`
        - `def get_us_inflation_yoy_pct(self) -> float | None:`
        - `def get_us_inflation_yoy_pct(self) -> float | None:`
        - `def get_macro_snapshot(self, base_currency: str) -> dict:`

        ### `backend/app/clients/market_client.py`

        **Imports internos:**

        - `from app.core.decorators import log_execution_time`
        - `from app.core.market_utils import normalize_end_date_to_available_data, validate_not_future`
        - `from app.core.assets_registry import ASSET_METADATA_BY_TICKER`
        - `from app.core.settings import Settings`

        **Clases y funciones:**

        - `class MarketClient:`
        - `def __init__(self, settings: Settings) -> None:`
        - `def _download_prices(self, ticker: str, start: str, end: str) -> pd.DataFrame:`
        - `def _convert_ohlc_to_usd(self, prices: pd.DataFrame, ticker: str, start: str, end: str) -> pd.DataFrame:`
        - `def get_prices(self, ticker: str, start: str, end: str, convert_to_usd: bool = True) -> pd.DataFrame:`

        ### `backend/app/core/__init__.py`

        ### `backend/app/core/assets_registry.py`

        ### `backend/app/core/decorators.py`

        **Clases y funciones:**

        - `def log_execution_time(func):`
        - `def wrapper(*args, **kwargs):`

        ### `backend/app/core/dependencies.py`

        **Imports internos:**

        - `from app.db.database import get_db`
        - `from app.clients.macro_client import MacroClient`
        - `from app.clients.market_client import MarketClient`
        - `from app.core.settings import Settings, get_settings`
        - `from app.services.decision_service import DecisionService`
        - `from app.services.macro_service import MacroService`
        - `from app.services.market_service import MarketService`
        - `from app.services.portfolio_service import PortfolioService`
        - `from app.services.risk_service import RiskService`
        - `from app.services.technical_service import TechnicalService`
        - `from app.services.capm_service import CapmService`
        - `from app.services.decision_service import DecisionService`
        - `from app.services.investor_service import InvestorService`
        - `from app.services.assets_service import AssetsService`
        - `from app.services.benchmark_service import BenchmarkService`
        - `from app.services.help_service import HelpService`
        - `from app.services.returns_stats_service import ReturnsStatsService`
        - `from app.services.alerts_service import AlertsService`
        - `from app.services.garch_service import GarchService`

        **Clases y funciones:**

        - `def get_app_settings() -> Settings:`
        - `def get_market_client(settings: Settings = Depends(get_app_settings)) -> MarketClient:`
        - `def get_macro_client(settings: Settings = Depends(get_app_settings)) -> MacroClient:`
        - `def get_market_service(client: MarketClient = Depends(get_market_client)) -> MarketService:`
        - `def get_technical_service(client: MarketClient = Depends(get_market_client)) -> TechnicalService:`
        - `def get_risk_service(client: MarketClient = Depends(get_market_client)) -> RiskService:`
        - `def get_portfolio_service(client: MarketClient = Depends(get_market_client)) -> PortfolioService:`
        - `def get_macro_service(`
        - `def get_capm_service(`
        - `def get_decision_service(`
        - `def get_investor_service() -> InvestorService:`
        - `def get_assets_service() -> AssetsService:`
        - `def get_benchmark_service(`
        - `def get_help_service() -> HelpService:`
        - `def get_returns_stats_service(client: MarketClient = Depends(get_market_client)) -> ReturnsStatsService:`
        - `def get_alerts_service(client: MarketClient = Depends(get_market_client)) -> AlertsService:`
        - `def get_garch_service(client: MarketClient = Depends(get_market_client)) -> GarchService:`

        **Dependencias / inyección detectada:**

        - `from app.db.database import get_db`
        - `def get_market_client(settings: Settings = Depends(get_app_settings)) -> MarketClient:`
        - `def get_macro_client(settings: Settings = Depends(get_app_settings)) -> MacroClient:`
        - `def get_market_service(client: MarketClient = Depends(get_market_client)) -> MarketService:`
        - `def get_technical_service(client: MarketClient = Depends(get_market_client)) -> TechnicalService:`
        - `def get_risk_service(client: MarketClient = Depends(get_market_client)) -> RiskService:`
        - `def get_portfolio_service(client: MarketClient = Depends(get_market_client)) -> PortfolioService:`
        - `def get_macro_service(`
        - `client: MacroClient = Depends(get_macro_client),`
        - `market_client: MarketClient = Depends(get_market_client),`
        - `def get_capm_service(`
        - `market_client: MarketClient = Depends(get_market_client),`
        - `macro_service: MacroService = Depends(get_macro_service),`
        - `def get_decision_service(`
        - `risk_service: RiskService = Depends(get_risk_service),`
        - `portfolio_service: PortfolioService = Depends(get_portfolio_service),`
        - `capm_service: CapmService = Depends(get_capm_service),`
        - `def get_investor_service() -> InvestorService:`
        - `def get_assets_service() -> AssetsService:`
        - `def get_benchmark_service(`
        - `market_client: MarketClient = Depends(get_market_client),`
        - `macro_service: MacroService = Depends(get_macro_service),`
        - `def get_help_service() -> HelpService:`
        - `def get_returns_stats_service(client: MarketClient = Depends(get_market_client)) -> ReturnsStatsService:`
        - `def get_alerts_service(client: MarketClient = Depends(get_market_client)) -> AlertsService:`
        - `def get_garch_service(client: MarketClient = Depends(get_market_client)) -> GarchService:`

        ### `backend/app/core/error_catalog.py`

        ### `backend/app/core/exceptions.py`

        **Imports internos:**

        - `from app.core.error_catalog import ERROR_CATALOG`

        **Clases y funciones:**

        - `class AppBaseException(Exception):`
        - `def __init__(self, catalog_key: str, extra: dict | None = None) -> None:`
        - `class InvalidDateRangeError(AppBaseException):`
        - `def __init__(self) -> None:`
        - `class FutureDateError(AppBaseException):`
        - `def __init__(self) -> None:`
        - `class InvalidApiKeyError(AppBaseException):`
        - `def __init__(self) -> None:`
        - `class TickerNotFoundError(AppBaseException):`
        - `def __init__(self, ticker: str | None = None) -> None:`
        - `class InsufficientObsVarError(AppBaseException):`
        - `def __init__(self, required: int | None = None) -> None:`
        - `class InsufficientObsCapmError(AppBaseException):`
        - `def __init__(self, required: int | None = None) -> None:`
        - `class InsufficientObsPortfolioError(AppBaseException):`
        - `def __init__(self, required: int | None = None) -> None:`
        - `class ExternalApiFailureError(AppBaseException):`
        - `def __init__(self, source: str | None = None) -> None:`

        ### `backend/app/core/help_catalog.py`

        ### `backend/app/core/market_utils.py`

        **Imports internos:**

        - `from app.core.exceptions import FutureDateError, InvalidDateRangeError`

        **Clases y funciones:**

        - `def normalize_end_date_to_available_data(df: pd.DataFrame) -> pd.DataFrame:`
        - `def validate_not_future(start: str, end: str) -> None:`

        ### `backend/app/core/security.py`

        **Imports internos:**

        - `from app.core.exceptions import InvalidApiKeyError`
        - `from app.core.settings import get_settings`

        **Clases y funciones:**

        - `def require_internal_api_key(x_api_key: str | None = Header(default=None)) -> None:`

        ### `backend/app/core/settings.py`

        **Clases y funciones:**

        - `class Settings(BaseSettings):`
        - `def get_settings() -> Settings:`

        ### `backend/app/db/__init__.py`

        **Imports internos:**

        - `from app.db.database import Base, SessionLocal, engine, get_db, init_db`
        - `from app.db.models import Asset, Portfolio, PredictionLog, Price`

        **Dependencias / inyección detectada:**

        - `from app.db.database import Base, SessionLocal, engine, get_db, init_db`
        - `"get_db",`

        ### `backend/app/db/build_perri_universe.py`

        **Clases y funciones:**

        - `def classify_asset(ticker: str) -> str:`
        - `def expected_currency(ticker: str) -> str:`
        - `def expected_fx_ticker(currency: str) -> str | None:`
        - `def recommended_benchmark(asset_type: str) -> str:`
        - `def benchmark_description(asset_type: str) -> str:`
        - `def build_perri_universe() -> dict:`
        - `def main() -> None:`

        ### `backend/app/db/database.py`

        **Imports internos:**

        - `from app.core.settings import get_settings`
        - `import app.db.models  # noqa: F401`

        **Clases y funciones:**

        - `class Base(DeclarativeBase):`
        - `def _resolve_sqlite_url(database_url: str) -> str:`
        - `def get_db() -> Generator[Session, None, None]:`
        - `def init_db() -> None:`

        **Dependencias / inyección detectada:**

        - `def get_db() -> Generator[Session, None, None]:`

        ### `backend/app/db/import_perri_prices.py`

        **Imports internos:**

        - `from app.db.database import SessionLocal, init_db`
        - `from app.db.models import Asset, Price`
        - `from app.db.seed_db import seed_base_assets, seed_perri_assets`

        **Clases y funciones:**

        - `def _chunks(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:`
        - `def _normalize_date(value: Any) -> date:`
        - `def import_perri_prices(cache_path: Path = CACHE_PATH) -> dict[str, int]:`
        - `def main() -> None:`

        ### `backend/app/db/models.py`

        **Imports internos:**

        - `from app.db.database import Base`

        **Clases y funciones:**

        - `def utc_now() -> datetime:`
        - `class Asset(Base):`
        - `class Price(Base):`
        - `class Portfolio(Base):`
        - `class PredictionLog(Base):`

        ### `backend/app/db/seed_db.py`

        **Imports internos:**

        - `from app.db.database import SessionLocal, init_db`
        - `from app.db.models import Asset`

        **Clases y funciones:**

        - `def _load_perri_universe() -> list[dict[str, Any]]:`
        - `def _upsert_asset(db, payload: dict[str, Any]) -> str:`
        - `def seed_base_assets() -> tuple[int, int]:`
        - `def seed_perri_assets() -> tuple[int, int]:`
        - `def count_assets() -> int:`
        - `def main() -> None:`

        ### `backend/app/domain/__init__.py`

        ### `backend/app/jobs/__init__.py`

        ### `backend/app/jobs/run_perri_optimization.py`

        **Imports internos:**

        - `from app.db.database import SessionLocal, init_db`
        - `from app.services.perri_optimizer_service import PerriOptimizerService`

        **Clases y funciones:**

        - `def _json_default(value: Any) -> str:`
        - `def _primary_metrics(result: dict) -> dict:`
        - `def run_perri_optimization_job(`
        - `def main() -> None:`

        ### `backend/app/main.py`

        **Imports internos:**

        - `from app.api.router import api_router`
        - `from app.core.exceptions import AppBaseException`
        - `from app.core.settings import get_settings`
        - `from app.db.database import init_db`

        **Decoradores detectados:**

        - `@asynccontextmanager`
        - `@app.exception_handler(AppBaseException)`
        - `@app.get("/", tags=["Root"])`
        - `@app.get("/health", tags=["Health"])`

        **Clases y funciones:**

        - `async def lifespan(app: FastAPI):`
        - `async def app_base_exception_handler(request: Request, exc: AppBaseException) -> JSONResponse:`
        - `async def root() -> dict[str, str]:`
        - `async def health() -> dict[str, str]:`

        ### `backend/app/schemas/__init__.py`

        ### `backend/app/schemas/alerts.py`

        **Decoradores detectados:**

        - `@field_validator("ticker")`
        - `@classmethod`

        **Clases y funciones:**

        - `class AlertsResponseItem(BaseModel):`
        - `class AlertsResponse(BaseModel):`
        - `class AlertsRequestParams(BaseModel):`
        - `def validate_ticker(cls, v: str) -> str:`

        ### `backend/app/schemas/benchmark.py`

        **Decoradores detectados:**

        - `@field_validator("tickers")`
        - `@classmethod`
        - `@field_validator("weights")`
        - `@classmethod`
        - `@field_validator("base_currency")`
        - `@classmethod`
        - `@field_validator("return_type")`
        - `@classmethod`
        - `@field_validator("mode")`
        - `@classmethod`

        **Clases y funciones:**

        - `class BenchmarkCompareRequest(BaseModel):`
        - `def validate_tickers(cls, v: list[str]) -> list[str]:`
        - `def validate_weights_sum(cls, v: list[float]) -> list[float]:`
        - `def validate_currency(cls, v: str) -> str:`
        - `def validate_return_type(cls, v: str) -> str:`
        - `def validate_mode(cls, v: str) -> str:`
        - `class BenchmarkMetrics(BaseModel):`
        - `class BenchmarkCompareResponse(BaseModel):`

        ### `backend/app/schemas/capm.py`

        **Decoradores detectados:**

        - `@field_validator("tickers")`
        - `@classmethod`
        - `@field_validator("weights")`
        - `@classmethod`
        - `@field_validator("base_currency")`
        - `@classmethod`
        - `@field_validator("return_type")`
        - `@classmethod`

        **Clases y funciones:**

        - `class CapmRegressionPoint(BaseModel):`
        - `class CapmResponse(BaseModel):`
        - `class PortfolioCapmRequest(BaseModel):`
        - `def validate_tickers(cls, v: list[str]) -> list[str]:`
        - `def validate_weights_sum(cls, v: list[float]) -> list[float]:`
        - `def validate_currency(cls, v: str) -> str:`
        - `def validate_return_type(cls, v: str) -> str:`
        - `class PortfolioCapmResponse(BaseModel):`

        ### `backend/app/schemas/common.py`

        **Decoradores detectados:**

        - `@field_validator("base_currency")`
        - `@classmethod`
        - `@field_validator("return_type")`
        - `@classmethod`

        **Clases y funciones:**

        - `class AssetItem(BaseModel):`
        - `class AssetsResponse(BaseModel):`
        - `class MacroQueryParams(BaseModel):`
        - `def validate_base_currency(cls, v: str) -> str:`
        - `class ReturnTypeMixin(BaseModel):`
        - `def validate_return_type(cls, v: str) -> str:`
        - `class AssetUniverseItem(BaseModel):`
        - `class AssetUniverseResponse(BaseModel):`
        - `class AssetSearchResponse(BaseModel):`

        ### `backend/app/schemas/decision.py`

        **Decoradores detectados:**

        - `@field_validator("tickers")`
        - `@classmethod`
        - `@field_validator("weights")`
        - `@classmethod`
        - `@field_validator("base_currency")`
        - `@classmethod`
        - `@field_validator("return_type")`
        - `@classmethod`

        **Clases y funciones:**

        - `class DecisionPanelRequest(BaseModel):`
        - `def validate_tickers(cls, v: list[str]) -> list[str]:`
        - `def validate_weights_sum(cls, v: list[float]) -> list[float]:`
        - `def validate_currency(cls, v: str) -> str:`
        - `def validate_return_type(cls, v: str) -> str:`
        - `class DecisionPanelResponse(BaseModel):`

        ### `backend/app/schemas/error.py`

        **Clases y funciones:**

        - `class ErrorDetail(BaseModel):`
        - `class ErrorResponse(BaseModel):`

        ### `backend/app/schemas/garch.py`

        **Decoradores detectados:**

        - `@field_validator("ticker")`
        - `@classmethod`
        - `@field_validator("return_type")`
        - `@classmethod`
        - `@field_validator("mode")`
        - `@classmethod`
        - `@field_validator("distribution")`
        - `@classmethod`

        **Clases y funciones:**

        - `class GarchRequest(BaseModel):`
        - `def validate_ticker(cls, v: str) -> str:`
        - `def validate_return_type(cls, v: str) -> str:`
        - `def validate_mode(cls, v: str) -> str:`
        - `def validate_distribution(cls, v: str) -> str:`
        - `class GarchModelResult(BaseModel):`
        - `class GarchForecastPoint(BaseModel):`
        - `class GarchResponse(BaseModel):`

        ### `backend/app/schemas/help.py`

        **Clases y funciones:**

        - `class HelpItem(BaseModel):`
        - `class HelpCatalogResponse(BaseModel):`

        ### `backend/app/schemas/investor.py`

        **Decoradores detectados:**

        - `@field_validator("tickers")`
        - `@classmethod`
        - `@field_validator("weights_pct")`
        - `@classmethod`
        - `@field_validator("base_currency")`
        - `@classmethod`
        - `@field_validator("risk_profile")`
        - `@classmethod`
        - `@field_validator("horizon_type")`
        - `@classmethod`
        - `@field_validator("return_type")`
        - `@classmethod`
        - `@field_validator("mode")`
        - `@classmethod`
        - `@model_validator(mode="after")`

        **Clases y funciones:**

        - `class InvestorPreferencesRequest(BaseModel):`
        - `def validate_tickers(cls, v: list[str]) -> list[str]:`
        - `def validate_weights_pct_range(cls, v: list[float]) -> list[float]:`
        - `def validate_currency(cls, v: str) -> str:`
        - `def validate_risk_profile(cls, v: str) -> str:`
        - `def validate_horizon_type(cls, v: str) -> str:`
        - `def validate_return_type(cls, v: str) -> str:`
        - `def validate_mode(cls, v: str) -> str:`
        - `def validate_cross_fields(self) -> "InvestorPreferencesRequest":`
        - `class InvestorPreferencesResponse(BaseModel):`

        ### `backend/app/schemas/macro.py`

        **Clases y funciones:**

        - `class MacroSnapshotResponse(BaseModel):`
        - `class FxSpotResponse(BaseModel):`

        ### `backend/app/schemas/market.py`

        **Clases y funciones:**

        - `class PricePoint(BaseModel):`
        - `class PricesResponse(BaseModel):`
        - `class ReturnPoint(BaseModel):`
        - `class ReturnsResponse(BaseModel):`

        ### `backend/app/schemas/portfolio.py`

        **Decoradores detectados:**

        - `@model_validator(mode="before")`
        - `@classmethod`
        - `@field_validator("tickers")`
        - `@classmethod`
        - `@field_validator("return_type")`
        - `@classmethod`
        - `@field_validator("risk_profile")`
        - `@classmethod`

        **Clases y funciones:**

        - `class EfficientFrontierRequest(BaseModel):`
        - `def map_frontend_aliases(cls, values: dict):`
        - `def validate_tickers(cls, v: list[str]) -> list[str]:`
        - `def validate_return_type(cls, v: str) -> str:`
        - `def validate_risk_profile(cls, v: str | None) -> str | None:`
        - `class FrontierPoint(BaseModel):`
        - `class PortfolioWeightsItem(BaseModel):`
        - `class OptimalPortfolio(BaseModel):`
        - `class TargetReturnPortfolio(BaseModel):`
        - `class ProfileSuggestedPortfolio(BaseModel):`
        - `class TopPortfolio(BaseModel):`
        - `class EfficientFrontierResponse(BaseModel):`

        ### `backend/app/schemas/returns_stats.py`

        **Decoradores detectados:**

        - `@field_validator("ticker")`
        - `@classmethod`
        - `@field_validator("return_type")`
        - `@classmethod`
        - `@field_validator("mode")`
        - `@classmethod`

        **Clases y funciones:**

        - `class ReturnsStatsRequest(BaseModel):`
        - `def validate_ticker(cls, v: str) -> str:`
        - `def validate_return_type(cls, v: str) -> str:`
        - `def validate_mode(cls, v: str) -> str:`
        - `class NormalityTestResult(BaseModel):`
        - `class AndersonDarlingResult(BaseModel):`
        - `class HistogramBin(BaseModel):`
        - `class QQPoint(BaseModel):`
        - `class BoxplotSummary(BaseModel):`
        - `class ReturnsStatsResponse(BaseModel):`

        ### `backend/app/schemas/risk.py`

        **Decoradores detectados:**

        - `@field_validator("weights")`
        - `@classmethod`
        - `@field_validator("tickers")`
        - `@classmethod`
        - `@field_validator("return_type")`
        - `@classmethod`
        - `@field_validator("distribution")`
        - `@classmethod`

        **Clases y funciones:**

        - `class PortfolioVarRequest(BaseModel):`
        - `def validate_weights_sum(cls, v: list[float]) -> list[float]:`
        - `def validate_tickers_not_empty(cls, v: list[str]) -> list[str]:`
        - `def validate_return_type(cls, v: str) -> str:`
        - `def validate_distribution(cls, v: str) -> str:`
        - `class VarMethodResult(BaseModel):`
        - `class KupiecBacktestResult(BaseModel):`
        - `class PortfolioVarResponse(BaseModel):`

        ### `backend/app/schemas/technical.py`

        **Clases y funciones:**

        - `class TechnicalPoint(BaseModel):`
        - `class TechnicalResponse(BaseModel):`

        ### `backend/app/schemas/valuation.py`

        **Clases y funciones:**

        - `class YieldCurveRequest(BaseModel):`
        - `class NelsonSiegelParams(BaseModel):`
        - `class YieldCurveResponse(BaseModel):`
        - `class OptionValuationRequest(BaseModel):`
        - `class Greeks(BaseModel):`
        - `class OptionValuationResponse(BaseModel):`

        ### `backend/app/services/__init__.py`

        ### `backend/app/services/alerts_service.py`

        **Imports internos:**

        - `from app.clients.market_client import MarketClient`
        - `from app.core.exceptions import TickerNotFoundError`

        **Clases y funciones:**

        - `class AlertsService:`
        - `def __init__(self, client: MarketClient) -> None:`
        - `def _load_data(self, ticker: str, start: str, end: str) -> pd.DataFrame:`
        - `def get_alerts(`

        ### `backend/app/services/assets_service.py`

        **Imports internos:**

        - `from app.core.assets_registry import ALL_ASSETS`
        - `from app.db.models import Asset`

        **Clases y funciones:**

        - `class AssetsService:`
        - `def _asset_to_item(self, asset: Asset, default_tickers: set[str]) -> dict:`
        - `def _fallback_assets(self) -> list[dict]:`
        - `def list_assets(self, db: Session | None = None) -> list[dict]:`
        - `def search_assets(self, query: str, db: Session | None = None) -> dict:`
        - `def summarize_assets(self, db: Session) -> dict:`

        ### `backend/app/services/benchmark_service.py`

        **Imports internos:**

        - `from app.clients.market_client import MarketClient`
        - `from app.services.macro_service import MacroService`

        **Clases y funciones:**

        - `class BenchmarkService:`
        - `def __init__(self, market_client: MarketClient, macro_service: MacroService) -> None:`
        - `def _returns(self, ticker: str, start: str, end: str, return_type: str) -> pd.Series:`
        - `def _returns_matrix(self, tickers: list[str], start: str, end: str, return_type: str) -> pd.DataFrame:`
        - `def _cumulative_return(self, returns: pd.Series, return_type: str) -> float:`
        - `def _annual_return(self, returns: pd.Series, return_type: str) -> float:`
        - `def _annual_volatility(self, returns: pd.Series) -> float:`
        - `def _max_drawdown(self, returns: pd.Series, return_type: str) -> float:`
        - `def _metrics(self, returns: pd.Series, rf_decimal: float, return_type: str) -> dict:`
        - `def compare(`

        ### `backend/app/services/capm_service.py`

        **Imports internos:**

        - `from app.clients.market_client import MarketClient`
        - `from app.services.macro_service import MacroService`

        **Clases y funciones:**

        - `class CapmService:`
        - `def __init__(self, market_client: MarketClient, macro_service: MacroService) -> None:`
        - `def _returns(self, ticker: str, start: str, end: str, return_type: str) -> pd.Series:`
        - `def _returns_matrix(self, tickers: list[str], start: str, end: str, return_type: str) -> pd.DataFrame:`
        - `def _classify_beta(beta: float) -> str:`
        - `def calculate_capm(`
        - `def calculate_portfolio_capm(`

        ### `backend/app/services/decision_service.py`

        **Imports internos:**

        - `from app.services.capm_service import CapmService`
        - `from app.services.portfolio_service import PortfolioService`
        - `from app.services.risk_service import RiskService`

        **Clases y funciones:**

        - `class DecisionService:`
        - `def __init__(`
        - `def _infer_stance(self, portfolio_beta: float, alpha_simple: float, mc_var_daily: float) -> str:`
        - `def build_panel(`

        ### `backend/app/services/garch_service.py`

        **Imports internos:**

        - `from app.clients.market_client import MarketClient`
        - `from app.core.exceptions import TickerNotFoundError`

        **Clases y funciones:**

        - `class GarchService:`
        - `def __init__(self, client: MarketClient) -> None:`
        - `def _get_returns(self, ticker: str, start: str, end: str, return_type: str) -> pd.Series:`
        - `def _safe_float_list(values) -> list[float]:`
        - `def _normalize_distribution(distribution: str) -> str:`
        - `def _distribution_label(distribution: str) -> str:`
        - `def analyze(`

        ### `backend/app/services/help_service.py`

        **Imports internos:**

        - `from app.core.help_catalog import HELP_CATALOG`

        **Clases y funciones:**

        - `class HelpService:`
        - `def get_catalog(self) -> dict:`

        ### `backend/app/services/investor_service.py`

        **Imports internos:**

        - `from app.schemas.investor import InvestorPreferencesRequest`

        **Clases y funciones:**

        - `class InvestorService:`
        - `def determine_risk_profile(self, kyc_answers: dict) -> str:`
        - `def resolve_horizon(self, payload: InvestorPreferencesRequest) -> dict:`

        ### `backend/app/services/macro_service.py`

        **Imports internos:**

        - `from app.clients.macro_client import MacroClient`
        - `from app.clients.market_client import MarketClient`

        **Clases y funciones:**

        - `class MacroService:`
        - `def __init__(self, client: MacroClient, market_client: MarketClient) -> None:`
        - `def get_macro_snapshot(self, base_currency: str) -> dict:`
        - `def resolve_rf_inputs(self, base_currency: str) -> tuple[str, float]:`
        - `def get_fx_spot(self, base_currency: str) -> dict:`

        ### `backend/app/services/market_service.py`

        **Imports internos:**

        - `from app.clients.market_client import MarketClient`
        - `from app.db.models import Asset, Price`

        **Clases y funciones:**

        - `class MarketService:`
        - `def __init__(self, client: MarketClient) -> None:`
        - `def _get_prices_from_db(`
        - `def get_prices(`
        - `def get_returns(`

        ### `backend/app/services/option_service.py`

        **Clases y funciones:**

        - `class OptionService:`
        - `def calculate_black_scholes(`
        - `def implied_volatility(self, target_price: float, S: float, K: float, T: float, r: float) -> float:`

        ### `backend/app/services/perri_optimizer_service.py`

        **Imports internos:**

        - `from app.db.models import Asset, Price`

        **Clases y funciones:**

        - `class PerriOptimizerService:`
        - `def __init__(`
        - `def _get_end_date(self, db: Session, end: str | None) -> pd.Timestamp:`
        - `def _window_for_horizon(`
        - `def _load_eligible_assets(self, db: Session) -> list[Asset]:`
        - `def _load_asset_by_ticker(self, db: Session, ticker: str) -> Asset | None:`
        - `def _load_close_series(`
        - `def _to_returns(self, close: pd.Series) -> pd.Series:`
        - `def _build_returns_by_asset(`
        - `def _load_benchmark_returns(`
        - `def _individual_metrics(`
        - `def _candidate_sets(self, metrics: pd.DataFrame, portfolio_size: int) -> dict[str, list[str]]:`
        - `def _build_aligned_returns_matrix(`
        - `def _portfolio_metrics(`
        - `def _capm_metrics(`
        - `def _distribution_by_asset_type(`
        - `def _weights_payload(self, tickers: list[str], weights: np.ndarray) -> list[dict[str, float | str]]:`
        - `def _optimize_once(`
        - `def objective(weights: np.ndarray) -> float:`
        - `def _optimize_for_size(`
        - `def _optimize_for_horizon(`
        - `def run_optimization(`

        ### `backend/app/services/portfolio_service.py`

        **Imports internos:**

        - `from app.clients.market_client import MarketClient`

        **Clases y funciones:**

        - `class PortfolioOptimizerSingleton:`
        - `def __new__(cls, *args, **kwargs):`
        - `def __init__(self, client: MarketClient | None = None):`
        - `def _get_returns_matrix(self, tickers: list[str], start: str, end: str) -> pd.DataFrame:`
        - `def optimize_markowitz(`
        - `def portfolio_volatility(weights: np.ndarray) -> float:`
        - `class PortfolioService:`
        - `def __init__(self, client: MarketClient) -> None:`
        - `def _returns_by_type(self, close: pd.Series, return_type: str) -> pd.Series:`
        - `def _build_returns_matrix(`
        - `def _annual_return_from_daily(self, daily_return: float, return_type: str) -> float:`
        - `def _portfolio_metrics(`
        - `def _weights_payload(self, tickers: list[str], weights: np.ndarray) -> list[dict]:`
        - `def _portfolio_payload(`
        - `def _simulate_portfolios(`
        - `def _build_frontier_points(self, simulated: list[dict]) -> list[dict]:`
        - `def _optimize_min_variance(`
        - `def objective(weights: np.ndarray) -> float:`
        - `def _optimize_max_sharpe(`
        - `def objective(weights: np.ndarray) -> float:`
        - `def _select_target_return_portfolio(`
        - `def _select_profile_portfolio(`
        - `def _select_top_portfolios(`
        - `def build_efficient_frontier(`

        ### `backend/app/services/returns_stats_service.py`

        **Imports internos:**

        - `from app.clients.market_client import MarketClient`
        - `from app.core.exceptions import TickerNotFoundError`

        **Clases y funciones:**

        - `class ReturnsStatsService:`
        - `def __init__(self, client: MarketClient) -> None:`
        - `def _get_returns(self, ticker: str, start: str, end: str, return_type: str) -> pd.Series:`
        - `def _normality_conclusion(self, p_value: float | None) -> str:`
        - `def build_returns_stats(`

        ### `backend/app/services/risk_service.py`

        **Imports internos:**

        - `from app.clients.market_client import MarketClient`

        **Clases y funciones:**

        - `class RiskService:`
        - `def __init__(self, client: MarketClient) -> None:`
        - `def _build_returns_matrix(self, tickers: list[str], start: str, end: str, return_type: str) -> pd.DataFrame:`
        - `def _portfolio_returns(self, returns_df: pd.DataFrame, weights: list[float]) -> pd.Series:`
        - `def _normalize_distribution(distribution: str) -> str:`
        - `def _distribution_label(distribution: str) -> str:`
        - `def _historical_var_cvar(self, portfolio_returns: pd.Series, alpha: float) -> dict:`
        - `def _monte_carlo_var_cvar(`
        - `def _parametric_var_cvar(`
        - `def _kupiec_test(self, portfolio_returns: pd.Series, alpha: float, var_daily: float) -> dict:`
        - `def calculate_var(`

        ### `backend/app/services/roboadvisor_service.py`

        **Imports internos:**

        - `from app.services.portfolio_service import PortfolioOptimizerSingleton`
        - `from app.clients.market_client import MarketClient`

        **Clases y funciones:**

        - `class RoboAdvisorService:`
        - `def __init__(self, market_client: MarketClient):`
        - `def suggest_hybrid_portfolio(self, profile: str, total_assets: int, custom_tickers: list[str] = None) -> dict:`

        ### `backend/app/services/technical_service.py`

        **Imports internos:**

        - `from app.clients.market_client import MarketClient`

        **Clases y funciones:**

        - `class TechnicalService:`
        - `def __init__(self, client: MarketClient) -> None:`
        - `def get_indicators(self, ticker: str, start: str, end: str) -> pd.DataFrame:`

        ### `backend/app/services/yield_service.py`

        **Clases y funciones:**

        - `class YieldService:`
        - `def nelson_siegel(t: np.ndarray, tau: float, beta0: float, beta1: float, beta2: float) -> np.ndarray:`
        - `def fit_nelson_siegel(self, yields: list[float], maturities: list[float]) -> dict:`
        - `def objective(params):`

        ### `frontend/app.py`

        **Clases y funciones:**

        - `def verificar_login(username, password):`

        ### `frontend/config.py`

        ### `frontend/pages/01_Tecnico.py`

        **Clases y funciones:**

        - `def _fetch_assets_and_help() -> tuple[list[dict], dict[str, dict], str | None]:`
        - `def _resolve_dates(`
        - `def _fetch_prices(ticker: str, start: str, end: str) -> tuple[pd.DataFrame, str | None]:`
        - `def _build_technical_view(`
        - `def _latest_valid(series: pd.Series) -> float | None:`
        - `def _previous_valid(series: pd.Series) -> float | None:`
        - `def _format_delta(current: float | None, previous: float | None, as_pct: bool = True) -> str:`
        - `def _interpret_trend(close_now: float | None, sma_now: float | None, ema_now: float | None) -> str:`
        - `def _interpret_rsi(rsi_now: float | None) -> str:`
        - `def _interpret_bollinger(close_now: float | None, bb_low: float | None, bb_up: float | None) -> str:`
        - `def _interpret_macd(macd_now: float | None, signal_now: float | None, hist_now: float | None) -> str:`
        - `def _interpret_stochastic(stoch_k_now: float | None, stoch_d_now: float | None) -> str:`
        - `def _plot_price_ma(df: pd.DataFrame,modo: str,sma_window: int,ema_window: int,show_price: bool,show_sma: bool,show_ema: bool,`
        - `def _plot_rsi(df: pd.DataFrame, modo: str, rsi_window: int, show_levels: bool) -> go.Figure:`
        - `def _plot_bollinger(`
        - `def _plot_macd(`
        - `def _plot_stochastic(`

        ### `frontend/pages/02_Rendimientos.py`

        **Clases y funciones:**

        - `def _fetch_assets_and_help() -> tuple[list[dict], dict[str, dict], str | None]:`
        - `def _resolve_dates(`
        - `def _fetch_returns_stats(`
        - `def _fetch_raw_returns(`
        - `def _normal_pdf(x: np.ndarray, mean: float, std: float) -> np.ndarray:`
        - `def _build_histogram_figure(`
        - `def _build_boxplot_figure(`
        - `def _extract_qq_df(payload: dict) -> pd.DataFrame:`
        - `def pick(*names):`
        - `def _build_qq_figure(qq_df: pd.DataFrame, modo: str) -> go.Figure:`
        - `def _render_test_card(`
        - `def _help_badge(text: str):`

        ### `frontend/pages/03_Garch.py`

        **Clases y funciones:**

        - `def _fetch_assets_and_help() -> tuple[list[dict], dict[str, dict], str | None]:`
        - `def _resolve_dates(`
        - `def _fetch_garch(`
        - `def _format_comparison_table(candidate_models: list[dict]) -> pd.DataFrame:`
        - `def _extract_best_log_likelihood(payload: dict):`
        - `def _format_diagnostics_table(payload: dict) -> pd.DataFrame:`
        - `def _fmt(v):`
        - `def _extract_best_model_series(payload: dict) -> pd.DataFrame:`
        - `def _extract_multi_model_series(payload: dict) -> pd.DataFrame:`
        - `def _build_conditional_volatility_figure(payload: dict, modo: str) -> tuple[go.Figure, bool]:`
        - `def compact_help_card(title: str, help_text: str, caption: str = ""):`
        - `def _extract_forecast_df(payload: dict) -> pd.DataFrame:`
        - `def _build_forecast_figure(`
        - `def _forecast_message(payload: dict) -> str:`
        - `def _diagnostic_guide(payload: dict) -> str:`
        - `def _format_num(valor, decimales=4):`
        - `def _format_pct(valor):`

        ### `frontend/pages/04_Capm.py`

        **Clases y funciones:**

        - `def _resolve_dates(`
        - `def _pick_value(payload: dict | None, *keys):`
        - `def _asset_options() -> tuple[list[str], dict[str, dict]]:`
        - `def _weights_editor(sidebar_container, key_prefix: str) -> tuple[list[float], float]:`
        - `def _fetch_capm(`
        - `def _fetch_portfolio_capm(`
        - `def _coerce_series_frame(payload: dict) -> pd.DataFrame:`
        - `def pick(*names):`
        - `def _build_regression_figure(`
        - `def _format_capm_table(payload: dict) -> pd.DataFrame:`
        - `def _fmt(v):`
        - `def _classify_beta(beta: float | None) -> str:`
        - `def _expected_return_text(v) -> str:`
        - `def _format_num(x, ndigits: int = 4) -> str:`
        - `def _capm_reading(payload: dict) -> str:`

        ### `frontend/pages/05_Var_Cvar.py`

        **Clases y funciones:**

        - `def _resolve_dates(`
        - `def _weights_editor(sidebar_container, key_prefix: str) -> tuple[list[float], float]:`
        - `def _format_pct(x) -> str:`
        - `def _format_num(x, ndigits: int = 4) -> str:`
        - `def _format_money(x) -> str:`
        - `def _money_risk(portfolio_value: float, risk_pct) -> float | None:`
        - `def _fetch_var(`
        - `def _method_metric(payload: dict, method_key: str, *metric_names):`
        - `def _extract_distribution_series(payload: dict) -> pd.Series:`
        - `def _extract_kupiec(payload: dict) -> dict:`
        - `def _comparison_table(payload: dict, portfolio_value: float) -> pd.DataFrame:`
        - `def _build_distribution_figure(`

        ### `frontend/pages/06_Markowitz.py`

        **Clases y funciones:**

        - `def _resolve_dates(`
        - `def _pick_value(payload: dict | None, *keys):`
        - `def _format_pct(x) -> str:`
        - `def _format_num(x, ndigits: int = 4) -> str:`
        - `def _format_money(x) -> str:`
        - `def _profile_to_backend(profile_label: str) -> str | None:`
        - `def _weights_editor(`
        - `def _fetch_rf_usd() -> tuple[float, str, str | None]:`
        - `def _build_frontier_payload(`
        - `def _fetch_frontier(payload: dict) -> tuple[dict, str | None]:`
        - `def _extract_frontier_df(payload: dict) -> pd.DataFrame:`
        - `def pick(*names):`
        - `def _extract_simulated_df(payload: dict) -> pd.DataFrame:`
        - `def pick(*names):`
        - `def _extract_named_block(payload: dict, *keys) -> dict:`
        - `def _extract_min_var(payload: dict) -> dict:`
        - `def _extract_max_sharpe(payload: dict) -> dict:`
        - `def _extract_target(payload: dict) -> dict:`
        - `def _extract_profile_suggestion(payload: dict) -> dict:`
        - `def _extract_weights_df(obj: dict | None) -> pd.DataFrame:`
        - `def _extract_reference_weights_df(weights: list[float]) -> pd.DataFrame:`
        - `def _extract_top_portfolios_df(payload: dict) -> pd.DataFrame:`
        - `def _extract_corr_df(payload: dict) -> pd.DataFrame:`
        - `def _metric_from_block(block: dict, *keys):`
        - `def _selected_portfolio_block(`
        - `def _selected_return_and_vol(block: dict) -> tuple[float | None, float | None]:`
        - `def _build_corr_heatmap(corr_df: pd.DataFrame, modo: str, clean_view: bool) -> go.Figure:`
        - `def _build_frontier_figure(`
        - `def _module_reading(`

        ### `frontend/pages/07_Señales.py`

        **Clases y funciones:**

        - `def _resolve_dates(`
        - `def _safe_str(v) -> str:`
        - `def _safe_float(v) -> float | None:`
        - `def _pick_value(payload: dict | None, *keys):`
        - `def _extract_alert_items(payload: dict) -> list[dict]:`
        - `def _fetch_alerts_for_asset(`
        - `def _infer_signal_status(alert: dict) -> tuple[str, str, str]:`
        - `def _human_title(alert: dict) -> str:`
        - `def _human_description(alert: dict) -> str:`
        - `def _human_date(alert: dict) -> str:`
        - `def _human_value(alert: dict) -> str:`
        - `def _render_signal_card(alert: dict):`
        - `def _build_summary_rows(asset_results: list[dict]) -> pd.DataFrame:`

        ### `frontend/pages/08_Macro_Benchmark.py`

        **Clases y funciones:**

        - `def _resolve_dates(`
        - `def _normalize_mode(modo: str) -> str:`
        - `def _pick_value(payload: dict | None, *keys):`
        - `def _format_pct(x) -> str:`
        - `def _format_num(x, ndigits: int = 4) -> str:`
        - `def _weights_editor(sidebar_container, key_prefix: str) -> tuple[list[float], float]:`
        - `def _call_macro_snapshot(client, base_currency: str) -> dict:`
        - `def _call_benchmark_compare(client, payload: dict) -> dict:`
        - `def _fetch_macro_and_benchmark(`
        - `def _metric_block(payload: dict, key: str) -> dict:`
        - `def _extract_macro_table(macro_payload: dict) -> pd.DataFrame:`
        - `def _comparison_table(benchmark_payload: dict) -> pd.DataFrame:`
        - `def _build_base100_chart(benchmark_payload: dict, modo: str, clean_view: bool) -> go.Figure:`

        ### `frontend/pages/0_Contextualizacion.py`

        **Clases y funciones:**

        - `def _get_logo_path(ticker: str) -> str | None:`
        - `def _build_asset_profile(name: str, ticker: str, country: str, is_default: bool) -> dict[str, str]:`
        - `def _fetch_assets_and_help() -> tuple[list[dict], dict[str, dict[str, str]], str | None]:`
        - `def _chunks(items: list[dict], size: int) -> list[list[dict]]:`
        - `def _render_logo_card(ticker: str):`
        - `def _render_role_card(profile: dict[str, str]):`
        - `def _render_financial_card(profile: dict[str, str], asset: dict):`
        - `def _render_asset_block(asset: dict, modo: str):`
        - `def _render_rf_and_benchmark_tab():`

        ### `frontend/services/api_client.py`

        **Clases y funciones:**

        - `class ApiConfig:`
        - `def api_root(self) -> str:`
        - `def _read_secret(key: str, default: str | None = None) -> str | None:`
        - `def get_api_config() -> ApiConfig:`
        - `class ApiClientError(Exception):`
        - `def __init__(`
        - `class ApiClient:`
        - `def __init__(self, config: ApiConfig | None = None) -> None:`
        - `def _headers(self, include_api_key: bool = False) -> dict[str, str]:`
        - `def _url(self, path: str) -> str:`
        - `def _handle_response(self, response: requests.Response) -> dict[str, Any]:`
        - `def get(`
        - `def post(`
        - `def get_root(self) -> dict[str, Any]:`
        - `def get_health(self) -> dict[str, Any]:`
        - `def get_assets(self) -> dict[str, Any]:`
        - `def search_assets(self, query: str) -> dict[str, Any]:`
        - `def get_help_catalog(self) -> dict[str, Any]:`
        - `def get_prices(self, ticker: str, start: str, end: str) -> dict[str, Any]:`
        - `def get_returns(self, ticker: str, start: str, end: str) -> dict[str, Any]:`
        - `def get_technical_indicators(`
        - `def get_returns_stats(`
        - `def get_alerts(`
        - `def get_garch(`
        - `def get_capm(`
        - `def get_portfolio_capm(self, payload: dict[str, Any]) -> dict[str, Any]:`
        - `def post_var_risk(self, payload: dict[str, Any]) -> dict[str, Any]:`
        - `def get_portfolio_var(self, payload: dict[str, Any]) -> dict[str, Any]:`
        - `def post_efficient_frontier(self, payload: dict[str, Any]) -> dict[str, Any]:`
        - `def get_efficient_frontier(self, payload: dict[str, Any]) -> dict[str, Any]:`
        - `def get_macro(self, base_currency: str = "USD") -> dict[str, Any]:`
        - `def get_macro_snapshot(self, base_currency: str = "USD") -> dict[str, Any]:`
        - `def get_fx_spot(self, base_currency: str = "USD") -> dict[str, Any]:`
        - `def post_benchmark_compare(self, payload: dict[str, Any]) -> dict[str, Any]:`
        - `def compare_benchmark(self, payload: dict[str, Any]) -> dict[str, Any]:`
        - `def get_decision_panel(self, payload: dict[str, Any]) -> dict[str, Any]:`
        - `def validate_investor_preferences(self, payload: dict[str, Any]) -> dict[str, Any]:`
        - `def get_perri_latest(self) -> dict[str, Any]:`
        - `def post_roboadvisor_suggest(self, payload: dict[str, Any]) -> dict[str, Any]:`
        - `def get_api_client() -> ApiClient:`

        ### `frontend/ui/__init__.py`

        ### `frontend/ui/cards.py`

        **Clases y funciones:**

        - `def render_chip(text: str):`
        - `def render_chip_row(items: list[str]):`
        - `def render_info_card(title: str, body: str):`
        - `def render_meta_row(items: list[tuple[str, str]]):`

        ### `frontend/ui/dashboard_filters.py`

        ### `frontend/ui/dashboard_ui.py`

        **Clases y funciones:**

        - `def aplicar_estilos_globales(modo: str = "General"):`
        - `def render_sidebar_brand(`
        - `def render_sidebar_panel(`
        - `def mode_badge(modo: str):`
        - `def header_dashboard(titulo: str, subtitulo: str, modo: str | None = None):`
        - `def nota(texto: str):`
        - `def seccion(titulo: str):`
        - `def titulo_con_ayuda(titulo: str, help_text: str, nivel: int = 3):`
        - `def tarjeta_kpi(`
        - `def plot_card_header(titulo: str, help_text: str, modo: str = "General", caption: str = ""):`
        - `def plot_card_footer(texto: str):`
        - `def toolbar_label(texto: str):`

        ### `frontend/ui/page_setup.py`

        **Clases y funciones:**

        - `def setup_dashboard_page(`

        ### `frontend/ui/plot_style.py`

        **Clases y funciones:**

        - `def style_plotly_figure(`
        - `def add_reference_line(`

        ### `frontend/ui/theme.py`

        **Clases y funciones:**

        - `def safe_text(text: str | None) -> str:`
        - `def image_to_base64(image_path: str) -> str:`
        - `def get_theme_tokens(modo: str = "General") -> dict[str, str]:`
        - `def build_global_css(modo: str = "General") -> str:`

        ### `tests/test_perri_horizons.py`

        **Imports internos:**

        - `from app.main import app  # noqa: E402`

        **Clases y funciones:**

        - `def test_perri_latest_contains_exact_horizons_sizes_and_objectives():`

        ### `tests/test_perri_latest.py`

        **Imports internos:**

        - `from app.main import app  # noqa: E402`

        **Clases y funciones:**

        - `def test_perri_latest_returns_precalculated_optimization():`

        ### `tests/test_perri_optimize.py`

        **Imports internos:**

        - `from app.main import app  # noqa: E402`

        **Clases y funciones:**

        - `def test_perri_optimize_returns_valid_portfolios():`
