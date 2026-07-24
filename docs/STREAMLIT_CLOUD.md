# Despliegue gratis en Streamlit Community Cloud

Esta configuración permite publicar el dashboard en `streamlit.app` usando el backend FastAPI integrado en el mismo proceso de Streamlit. No necesitas levantar un servidor adicional para la API si usas el modo por defecto.

## Configuración recomendada

- Repositorio: `edwardmorarom/Portafolio_APIS_RIESGO`
- Rama: `backend`
- Archivo principal: `frontend/app.py`
- Python: `3.11`

## API integrada

El frontend lee `BACKEND_BASE_URL`. Si no lo defines, usa:

```toml
BACKEND_BASE_URL = "inprocess"
```

En ese modo, las llamadas del dashboard se atienden con FastAPI mediante `TestClient`, sin depender de `http://127.0.0.1:8000`.

Si más adelante publicas el backend en otro servicio, puedes cambiar el secreto:

```toml
BACKEND_BASE_URL = "https://tu-backend-publico.com"
BACKEND_API_PREFIX = "/api/v1"
```

## Secrets opcionales

En Streamlit Cloud, abre `Advanced settings` y agrega solo los secretos que necesites:

```toml
BACKEND_BASE_URL = "inprocess"
BACKEND_API_PREFIX = "/api/v1"
APP_ENV = "prod"
DEBUG = "false"
LLM_PROVIDER = "local"
```

Si usas servicios externos, agrégalos también desde la interfaz de secretos, nunca en Git:

```toml
FRED_API_KEY = "..."
GROQ_API_KEY = "..."
GEMINI_API_KEY = "..."
```

## Pasos de publicación

1. Entra a `https://share.streamlit.io`.
2. Crea una app nueva desde GitHub.
3. Selecciona el repo `edwardmorarom/Portafolio_APIS_RIESGO`.
4. Selecciona la rama `backend`.
5. Usa `frontend/app.py` como archivo principal.
6. En `Advanced settings`, selecciona Python `3.11`.
7. Pega los secretos opcionales si los necesitas.
8. Haz clic en `Deploy`.

## Notas

- `backend/data/users.json` no debe subirse con datos reales de usuarios.
- `.env` y archivos `secrets.toml` locales están ignorados por Git.
- Streamlit Cloud instalará dependencias desde `frontend/requirements.txt` porque el entrypoint está en `frontend/app.py`.
