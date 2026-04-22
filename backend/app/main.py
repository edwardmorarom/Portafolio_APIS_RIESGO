from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.exceptions import AppBaseException
from app.core.settings import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="Backend del proyecto integrador de teoria del riesgo con FastAPI.",
)

allowed_origins = [item.strip() for item in settings.allowed_origins.split(",") if item.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppBaseException)
async def app_base_exception_handler(request: Request, exc: AppBaseException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": {
                "error_code": exc.error_code,
                "message": exc.message,
                "extra": exc.extra,
            }
        },
    )


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    return {
        "message": "Portafolio Riesgo API activa",
        "docs": "/docs",
        "version": settings.app_version,
    }


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "env": settings.app_env,
    }


app.include_router(api_router, prefix=settings.api_v1_prefix)