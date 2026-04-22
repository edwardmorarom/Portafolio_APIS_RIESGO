ERROR_CATALOG = {
    "INVALID_DATE_RANGE": {
        "status_code": 400,
        "error_code": "INVALID_DATE_RANGE",
        "message": "La fecha inicial debe ser menor que la fecha final.",
    },
    "FUTURE_DATE": {
        "status_code": 400,
        "error_code": "FUTURE_DATE",
        "message": "No se permiten fechas futuras.",
    },
    "INVALID_API_KEY": {
        "status_code": 401,
        "error_code": "INVALID_API_KEY",
        "message": "API key invalida o ausente.",
    },
    "TICKER_NOT_FOUND": {
        "status_code": 404,
        "error_code": "TICKER_NOT_FOUND",
        "message": "No se encontraron datos para el ticker solicitado.",
    },
    "INSUFFICIENT_OBS_VAR": {
        "status_code": 400,
        "error_code": "INSUFFICIENT_OBS_VAR",
        "message": "No hay suficientes observaciones para calcular VaR.",
    },
    "INSUFFICIENT_OBS_CAPM": {
        "status_code": 400,
        "error_code": "INSUFFICIENT_OBS_CAPM",
        "message": "No hay suficientes observaciones para calcular CAPM.",
    },
    "INSUFFICIENT_OBS_PORTFOLIO": {
        "status_code": 400,
        "error_code": "INSUFFICIENT_OBS_PORTFOLIO",
        "message": "No hay suficientes observaciones para optimizacion de portafolio.",
    },
    "EXTERNAL_API_FAILURE": {
        "status_code": 503,
        "error_code": "EXTERNAL_API_FAILURE",
        "message": "La API externa no respondio correctamente.",
    },
    "INVALID_PORTFOLIO_WEIGHTS": {
        "status_code": 400,
        "error_code": "INVALID_PORTFOLIO_WEIGHTS",
        "message": "Los pesos del portafolio son invalidos.",
    },
    "INVALID_CONFIDENCE_LEVEL": {
        "status_code": 400,
        "error_code": "INVALID_CONFIDENCE_LEVEL",
        "message": "El nivel de confianza enviado no es valido.",
    },
}