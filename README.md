# Portafolio Riesgo API

Backend y dashboard de integración para un proyecto de Teoría del Riesgo y APIs orientado al análisis de portafolios financieros con FastAPI y Streamlit.

El proyecto permite estudiar un portafolio internacional mediante precios históricos, rendimientos, indicadores técnicos, VaR/CVaR, CAPM, Markowitz, modelos ARCH/GARCH/EGARCH, señales técnicas, contexto macroeconómico y comparación contra benchmark.

---

## 1. Objetivo del proyecto

Construir una arquitectura separada entre backend y frontend para analizar un portafolio de activos internacionales desde una perspectiva financiera, estadística y de riesgo.

El backend se encarga de:

- Descargar datos de mercado.
- Validar entradas.
- Limpiar y transformar información.
- Convertir precios históricos a USD.
- Calcular modelos financieros y estadísticos.
- Exponer endpoints mediante FastAPI.

El frontend se encarga de:

- Visualizar resultados.
- Organizar filtros.
- Mostrar KPIs.
- Renderizar gráficas.
- Entregar interpretaciones para el usuario.
- Separar cada análisis en módulos de Streamlit.

---

## 2. Arquitectura general

```text
portafolio-riesgo/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── clients/
│   │   ├── core/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── requirements.txt
│   └── runtime.txt
├── frontend/
│   ├── assets/
│   ├── pages/
│   ├── services/
│   ├── ui/
│   ├── app.py
│   └── config.py
├── docs/
├── .env.example
├── .gitignore
└── README.md
```

---

## 3. Tecnologías principales

- FastAPI
- Streamlit
- Pydantic
- pydantic-settings
- yfinance
- pandas
- numpy
- scipy
- arch
- plotly
- uvicorn

---

## 4. Separación backend/frontend

El proyecto mantiene una separación clara:

### Backend

Contiene la lógica de negocio, datos y modelos:

- Descarga de precios desde yfinance.
- Conversión histórica de precios a USD.
- Validación de tickers, fechas, pesos y parámetros.
- Cálculo de rendimientos simples y logarítmicos.
- Indicadores técnicos.
- Estadísticas descriptivas.
- Pruebas de normalidad.
- VaR y CVaR.
- CAPM.
- Markowitz.
- ARCH/GARCH/EGARCH.
- Comparación contra benchmark.
- Señales técnicas.
- Snapshot macroeconómico.
- Manejo estructurado de errores.

### Frontend

Contiene la capa visual:

- Sidebar de filtros.
- Tarjetas KPI.
- Gráficas Plotly.
- Tablas.
- Interpretaciones.
- Componentes reutilizables de UI.
- Navegación modular por páginas.
- Diseño visual institucional.

---

## 5. Activos seleccionados

Activos base del proyecto:

| Activo | Ticker | País / Mercado |
|---|---|---|
| BP | `BP.L` | Reino Unido |
| Carrefour | `CA.PA` | Francia |
| Alimentation Couche-Tard | `ATD.TO` | Canadá |
| FEMSA | `FEMSAUBD.MX` | México |
| Seven & i | `3382.T` | Japón |

Justificación:

Se eligieron activos de diferentes geografías y perfiles empresariales para favorecer la diversificación y permitir un análisis comparativo internacional del riesgo, rendimiento, volatilidad y comportamiento frente al benchmark.

El universo puede ampliarse hasta un máximo de 15 activos por portafolio, según las restricciones del backend.

---

## 6. Conversión histórica a USD

Los activos internacionales pueden venir en monedas distintas según su mercado de cotización. Para evitar mezclar retornos de diferentes monedas dentro de una misma matriz de rendimientos, el backend convierte históricamente los precios a USD usando series de divisas de yfinance.

| Activo | Ticker | Moneda original | FX a USD |
|---|---|---|---|
| BP | `BP.L` | GBP/GBp | `GBPUSD=X` |
| Carrefour | `CA.PA` | EUR | `EURUSD=X` |
| Couche-Tard | `ATD.TO` | CAD | `CADUSD=X` |
| FEMSA | `FEMSAUBD.MX` | MXN | `MXNUSD=X` |
| Seven & i | `3382.T` | JPY | `JPYUSD=X` |

Esta conversión permite que los módulos de rendimientos, CAPM, VaR/CVaR, GARCH, Markowitz y benchmark trabajen bajo una moneda común.

---

## 7. Benchmark y moneda base

- Benchmark global por defecto: `ACWI`
- Moneda base metodológica: `USD`

El benchmark `ACWI` se utiliza porque el portafolio combina activos de distintos países. Por tanto, se requiere una referencia global y no un índice puramente local.

---

## 8. Tasa libre de riesgo

La tasa libre de riesgo principal se toma desde yfinance usando:

```text
^IRX
```

Esta referencia corresponde a Treasury Bill de 13 semanas y se usa como tasa corta en USD para métricas como:

- Sharpe.
- CAPM.
- Alpha de Jensen.
- Markowitz.

Se evita dejar una tasa libre de riesgo editable por el usuario en Markowitz para mantener consistencia metodológica.

---

## 9. Inflación

La inflación no se define manualmente.

El backend está preparado para calcular inflación anual YoY usando FRED y la serie:

```text
CPIAUCSL
```

Si no existe `FRED_API_KEY`, el backend devuelve `null` y el frontend muestra el indicador como no disponible.

Esto evita inventar datos macroeconómicos.

---

## 10. Módulos del dashboard

### Módulo 0 - Contextualización

Presenta:

- Activos base.
- Países.
- Rol financiero de cada activo.
- Conversión histórica a USD.
- Tasa libre de riesgo.
- Benchmark global.

### Módulo 1 - Análisis técnico

Incluye:

- Precio.
- SMA.
- EMA.
- RSI.
- Bandas de Bollinger.
- MACD.
- Línea de señal MACD.
- Histograma MACD.
- Oscilador Estocástico %K y %D.

También permite activar o desactivar capas de las gráficas.

### Módulo 2 - Rendimientos

Incluye:

- Rendimientos simples o logarítmicos.
- Estadísticas descriptivas.
- Histograma.
- Boxplot.
- Q-Q plot.
- Shapiro-Wilk.
- Jarque-Bera.
- Anderson-Darling cuando la muestra es apta.

### Módulo 3 - ARCH/GARCH/EGARCH

Incluye:

- ARCH.
- GARCH.
- EGARCH.
- Comparación por AIC/BIC.
- Diagnóstico de residuos.
- Volatilidad condicional.
- Pronóstico de volatilidad.

### Módulo 4 - CAPM

Incluye:

- Beta individual.
- Beta del portafolio.
- Alpha.
- R².
- P-value.
- Retorno esperado bajo CAPM.
- Regresión activo-benchmark.

### Módulo 5 - VaR y CVaR

Incluye:

- VaR histórico.
- VaR paramétrico.
- VaR Monte Carlo.
- CVaR histórico.
- CVaR paramétrico.
- CVaR Monte Carlo.
- VaR monetario.
- CVaR monetario.
- Test de Kupiec.

El nivel de confianza puede configurarse manualmente entre 95% y 99.99%.

### Módulo 6 - Markowitz

Incluye:

- Frontera eficiente.
- Matriz de correlación.
- Portafolio de mínima varianza.
- Portafolio de máximo Sharpe.
- Retorno objetivo.
- Valor del portafolio.
- Retorno esperado en dinero.
- Perfiles de inversionista.

Perfiles soportados:

- Sin perfil.
- Mínimo riesgo.
- Máxima utilidad.
- Arriesgado.

Cuando se selecciona un perfil o retorno objetivo, los pesos manuales se bloquean porque la composición debe salir del modelo de optimización.

### Módulo 7 - Señales técnicas

Convierte indicadores técnicos en alertas de compra, venta o neutralidad.

Indicadores utilizados:

- RSI.
- MACD.
- Bollinger.
- Medias móviles.
- Estocástico.

### Módulo 8 - Macro y benchmark

Incluye:

- Tasa libre de riesgo.
- Inflación si existe API key de FRED.
- Spot FX.
- Comparación del portafolio contra ACWI.
- Alpha de Jensen.
- Tracking Error.
- Information Ratio.
- Sharpe.
- Drawdown.

---

## 11. Variables de entorno

Crear un archivo `.env` a partir de `.env.example`.

En PowerShell:

```powershell
Copy-Item .env.example .env
Copy-Item .env backend\.env
```

Variables principales:

```env
APP_NAME=Portafolio Riesgo API
APP_VERSION=0.1.0
APP_ENV=dev
DEBUG=true

API_V1_PREFIX=/api/v1

DEFAULT_START_DATE=2021-01-01
DEFAULT_END_DATE=2026-12-31
GLOBAL_BENCHMARK=ACWI
DEFAULT_BASE_CURRENCY=USD

RF_TICKER_USD=^IRX
RF_TICKER_EUR=^GDBR10
RF_TICKER_COP_PROXY=^IRX

FRED_API_KEY=

FRONTEND_BASE_URL=http://localhost:8501
YAHOO_TIMEOUT_SECONDS=20
MACRO_TIMEOUT_SECONDS=20
EXTERNAL_API_TIMEOUT_SECONDS=20

INTERNAL_API_KEY=

ALLOWED_ORIGINS=http://localhost:8501,http://127.0.0.1:8501

MIN_OBS_VAR=60
MIN_OBS_CAPM=60
MIN_OBS_PORTFOLIO=60
```

Importante:

No subir `.env` a GitHub.

---

## 12. Instalación

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

### 4. Instalar dependencias del backend

```bash
cd backend
pip install -r requirements.txt
```

---

## 13. Ejecución del backend

Desde la carpeta `backend`:

```bash
uvicorn app.main:app --reload
```

La documentación automática queda disponible en:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

## 14. Ejecución del frontend

Desde la raíz del proyecto:

```bash
streamlit run frontend/app.py
```

El dashboard queda disponible en:

```text
http://localhost:8501
```

---

## 15. Endpoints principales

### Root y health

- `GET /`
- `GET /health`

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
- `GET /api/v1/macro/fx-spot/{base_currency}`

### Benchmark

- `POST /api/v1/benchmark/compare`

### Investor

- `POST /api/v1/investor/preferences`

### Decision

- `POST /api/v1/decision/panel`

### Help

- `GET /api/v1/help/catalog`

### Returns Stats

- `GET /api/v1/returns-stats/summary/{ticker}`

### Alerts

- `GET /api/v1/alerts/{ticker}`

### GARCH

- `GET /api/v1/garch/{ticker}`

---

## 16. Seguridad básica implementada

- Uso de `.env.example`.
- Exclusión de secretos con `.gitignore`.
- API key interna opcional para endpoints sensibles.
- Validación fuerte de inputs con Pydantic.
- Control de fechas futuras.
- Catálogo de errores.
- Respuestas estructuradas.
- Separación por routers, schemas, services y clients.

---

## 17. Notas metodológicas

- El sistema soporta rendimientos `simple` y `log`.
- Se validan pesos del portafolio.
- Se restringe el número máximo de activos.
- Se validan horizontes de análisis.
- Se soporta perfil del inversionista.
- Se soporta rendimiento objetivo en optimización.
- Se utiliza Rf común en USD para Markowitz y CAPM.
- Se evita mezclar monedas porque los precios se convierten históricamente a USD.
- La inflación solo se muestra si existe fuente real desde FRED.

---

## 18. Buenas prácticas implementadas

- Arquitectura modular.
- FastAPI para backend.
- Streamlit para frontend.
- Pydantic para validación.
- Pydantic Settings para configuración.
- Variables de entorno.
- Manejo de errores.
- Decoradores.
- Clientes externos.
- Servicios de negocio separados de rutas.
- Dashboard modular.
- Conversión histórica a USD.
- Documentación automática con Swagger.
- Componentes visuales reutilizables.
- Uso de tooltips para reducir texto visible en el dashboard.

---

## 19. Estado actual

Actualmente el proyecto implementa:

- Backend FastAPI modular.
- Frontend Streamlit modular.
- Precios y rendimientos reales.
- Conversión histórica a USD.
- Indicadores técnicos completos.
- VaR y CVaR porcentual y monetario.
- Frontera eficiente.
- CAPM por activo y portafolio.
- ARCH/GARCH/EGARCH.
- Benchmark compare.
- Panel de decisión.
- Preferencias del inversionista.
- Señales técnicas.
- Búsqueda de activos.
- Contexto macroeconómico con Rf real desde yfinance y soporte para inflación vía FRED.

---

## 20. Autores

- Edward Mora
- Juan P. Vargas