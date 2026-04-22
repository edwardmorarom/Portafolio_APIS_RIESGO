# Portafolio Riesgo API

Backend y base de integración para un proyecto de teoría del riesgo y APIs orientado al análisis de portafolios financieros con FastAPI.

## Objetivo

Construir una arquitectura separada entre backend y frontend para analizar un portafolio de activos mediante:

- precios históricos
- rendimientos simples y logarítmicos
- indicadores técnicos
- VaR y CVaR
- frontera eficiente
- CAPM por activo y por portafolio
- comparación contra benchmark
- contexto macroeconómico
- preferencias del inversionista

## Estructura del proyecto

portafolio-riesgo/
- backend/
  - app/
    - api/
    - clients/
    - core/
    - schemas/
    - services/
    - main.py
  - requirements.txt
- frontend/
- docs/
- .env.example
- .gitignore
- README.md

## Tecnologías principales

- FastAPI
- Pydantic
- yfinance
- pandas
- numpy
- scipy
- uvicorn

## Variables de entorno

Crear un archivo `.env` en la raíz o tomar como base `.env.example`.

Variables principales:

- `APP_NAME`
- `APP_VERSION`
- `APP_ENV`
- `DEBUG`
- `API_V1_PREFIX`
- `DEFAULT_START_DATE`
- `DEFAULT_END_DATE`
- `GLOBAL_BENCHMARK`
- `DEFAULT_BASE_CURRENCY`
- `RF_TICKER_USD`
- `RF_TICKER_EUR`
- `RF_TICKER_COP_PROXY`
- `FRED_API_KEY`
- `FRONTEND_BASE_URL`
- `YAHOO_TIMEOUT_SECONDS`
- `MACRO_TIMEOUT_SECONDS`
- `INTERNAL_API_KEY`
- `ALLOWED_ORIGINS`
- `MIN_OBS_VAR`
- `MIN_OBS_CAPM`
- `MIN_OBS_PORTFOLIO`

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/edwardmorarom/Portafolio_APIS_RIESGO.git
cd Portafolio_APIS_RIESGO
```

### 2. Crear entorno virtual

```bash
python -m venv .venv
```

### 3. Activar entorno virtual

En PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Instalar dependencias

```bash
cd backend
pip install -r requirements.txt
```

## Ejecución del backend

Desde la carpeta `backend`:

```bash
uvicorn app.main:app --reload
```

## Documentación automática

Con el backend levantado:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

## Endpoints principales

### Assets
- `GET /api/v1/assets/`
- `GET /api/v1/assets/search`

### Market
- `GET /api/v1/market/prices/{ticker}`
- `GET /api/v1/market/returns/{ticker}`

### Technical
- `GET /api/v1/technical/indicators/{ticker}`

### Risk
- `POST /api/v1/risk/var`

### Portfolio
- `POST /api/v1/portfolio/efficient-frontier`

### CAPM
- `GET /api/v1/capm/{ticker}`
- `POST /api/v1/capm/portfolio`

### Macro
- `GET /api/v1/macro/`

### Benchmark
- `POST /api/v1/benchmark/compare`

### Investor
- `POST /api/v1/investor/preferences`

### Decision
- `POST /api/v1/decision/panel`

## Activos predeterminados

El backend parte con estos activos por defecto:

- BP
- Carrefour
- Couche-Tard
- FEMSA
- Seven & i

Y permite un universo ampliado con máximo de 15 acciones por portafolio.

## Benchmark y monedas base

- Benchmark global por defecto: `ACWI`
- Monedas base soportadas:
  - USD
  - EUR
  - COP

Rf asociada:
- USD → `^TNX`
- EUR → `^GDBR10`
- COP → proxy con `^TNX`

## Seguridad básica implementada

- uso de `.env.example`
- exclusión de secretos con `.gitignore`
- API key interna opcional para endpoints sensibles
- validación fuerte de inputs con Pydantic
- control de fechas futuras
- catálogo de errores y respuestas estructuradas

## Notas metodológicas

- el sistema soporta rendimientos `simple` y `log`
- se validan pesos del portafolio
- se restringe el número máximo de activos
- se validan horizontes de análisis
- se soporta perfil del inversionista
- se soporta rendimiento objetivo en optimización

## Estado actual

Actualmente el backend ya implementa:

- arquitectura FastAPI modular
- precios y rendimientos reales
- indicadores técnicos
- VaR y CVaR
- frontera eficiente
- CAPM por activo y por portafolio
- benchmark compare
- panel de decisión
- preferencias del inversionista
- búsqueda de activos

## Autores

- Edward Mora
- [Nombre de tu compañera/o si aplica]

## Activos seleccionados

Activos base del proyecto:
- BP (`BP.L`)
- Carrefour (`CA.PA`)
- Alimentation Couche-Tard (`ATD.TO`)
- FEMSA (`FEMSAUBD.MX`)
- Seven & i (`3382.T`)

Justificación:
Se eligieron activos de diferentes geografías y perfiles empresariales para favorecer la diversificación y permitir un análisis comparativo internacional del riesgo, rendimiento, volatilidad y comportamiento frente al benchmark.

## Variables de entorno requeridas

Ejemplo base en `.env.example`.

Variables principales:
- `APP_NAME`
- `APP_VERSION`
- `APP_ENV`
- `DEBUG`
- `API_V1_PREFIX`
- `DEFAULT_START_DATE`
- `DEFAULT_END_DATE`
- `GLOBAL_BENCHMARK`
- `DEFAULT_BASE_CURRENCY`
- `RF_TICKER_USD`
- `RF_TICKER_EUR`
- `RF_TICKER_COP_PROXY`
- `FRED_API_KEY`
- `FRONTEND_BASE_URL`
- `YAHOO_TIMEOUT_SECONDS`
- `MACRO_TIMEOUT_SECONDS`
- `INTERNAL_API_KEY`
- `ALLOWED_ORIGINS`
- `MIN_OBS_VAR`
- `MIN_OBS_CAPM`
- `MIN_OBS_PORTFOLIO`

## Cómo ejecutar el frontend

Cuando la rama `frontend` esté lista:

```bash
streamlit run frontend/app.py
