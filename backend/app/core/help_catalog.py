HELP_CATALOG = {
    "sharpe_ratio": {
        "general": "Mide cuanto retorno obtiene el portafolio por cada unidad de riesgo asumido.",
        "estadistico": "Sharpe = (retorno anual - tasa libre de riesgo) / volatilidad anual.",
    },
    "max_drawdown": {
        "general": "Muestra la peor caida acumulada desde un maximo anterior.",
        "estadistico": "Es el minimo de la serie de drawdowns construida sobre la riqueza acumulada.",
    },
    "alpha_jensen": {
        "general": "Indica si el portafolio rindio mejor o peor de lo esperado frente al benchmark.",
        "estadistico": "Alpha de Jensen = retorno del portafolio - [rf + beta * (retorno benchmark - rf)].",
    },
    "tracking_error": {
        "general": "Mide que tanto se separa el portafolio de su benchmark.",
        "estadistico": "Es la desviacion estandar anualizada de los retornos activos.",
    },
    "information_ratio": {
        "general": "Resume si la diferencia frente al benchmark fue buena y consistente.",
        "estadistico": "Information Ratio = exceso de retorno sobre benchmark / tracking error.",
    },
    "var": {
        "general": "Estima una perdida probable bajo un nivel de confianza.",
        "estadistico": "VaR corresponde al cuantil de la distribucion de perdidas o retornos.",
    },
    "cvar": {
        "general": "Mide la perdida promedio en los peores escenarios.",
        "estadistico": "CVaR es la esperanza condicional de la cola mas extrema.",
    },
    "beta": {
        "general": "Mide cuanto se mueve un activo o portafolio frente al mercado.",
        "estadistico": "Beta = cov(retorno activo, retorno benchmark) / var(retorno benchmark).",
    },
    "rsi": {
        "general": "Ayuda a detectar posibles zonas de sobrecompra o sobreventa.",
        "estadistico": "Oscilador acotado entre 0 y 100 calculado con ganancias y perdidas medias.",
    },
    "macd": {
        "general": "Ayuda a detectar cambios en la fuerza o direccion de la tendencia.",
        "estadistico": "MACD = EMA rapida - EMA lenta; suele acompañarse de una linea senal.",
    },
    "bollinger_bands": {
        "general": "Muestran si el precio esta alto o bajo respecto a su comportamiento reciente.",
        "estadistico": "Bandas construidas con media movil y desviaciones estandar alrededor del precio.",
    },
    "confidence_level": {
        "general": "Es el nivel de certeza usado para estimar riesgo.",
        "estadistico": "Parametro de cola usado en VaR y CVaR, usualmente entre 0.95 y 0.99.",
    },
    "target_return": {
        "general": "Es la rentabilidad anual que el usuario quisiera alcanzar.",
        "estadistico": "Objetivo de retorno usado para seleccionar el portafolio mas cercano dentro del universo simulado.",
    },
}