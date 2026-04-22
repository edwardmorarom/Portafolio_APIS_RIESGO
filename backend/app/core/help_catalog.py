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
    "normalized_prices": {
        "general": "Permite comparar activos desde una misma base para ver cual ha rendido mejor.",
        "estadistico": "Reescala las series de precios a una base comun, usualmente 100, para comparar rendimientos relativos.",
    },
    "moving_averages": {
        "general": "Suavizan el precio para ayudar a ver la tendencia.",
        "estadistico": "Las medias moviles reducen ruido y facilitan identificar direccion y cruces de tendencia.",
    },
    "histogram_normal": {
        "general": "Compara la forma real de los rendimientos con una campana normal.",
        "estadistico": "Histograma de rendimientos con referencia gaussiana para evaluar asimetria, curtosis y colas.",
    },
    "qq_plot": {
        "general": "Sirve para ver si los rendimientos se parecen o no a una distribucion normal.",
        "estadistico": "Grafica cuantiles muestrales frente a cuantiles teoricos normales; desviaciones de la diagonal indican no normalidad.",
    },
    "boxplot": {
        "general": "Resume la dispersion, la mediana y los valores extremos.",
        "estadistico": "Muestra cuartiles, rango intercuartil y outliers segun la regla de 1.5 IQR.",
    },
    "var_cvar_distribution": {
        "general": "Ubica visualmente las perdidas de riesgo sobre la distribucion de retornos.",
        "estadistico": "Superpone niveles de VaR y CVaR sobre la distribucion para identificar cola de perdidas.",
    },
    "efficient_frontier": {
        "general": "Muestra las combinaciones de portafolio entre riesgo y retorno.",
        "estadistico": "Conjunto eficiente de Markowitz: maximo retorno esperado para cada nivel de volatilidad.",
    },
    "correlation_heatmap": {
        "general": "Ayuda a ver que activos se mueven parecido y cuales diversifican mejor.",
        "estadistico": "Mapa de calor de la matriz de correlacion entre activos; valores bajos reducen concentracion de riesgo.",
    },
    "garch_forecast": {
        "general": "Muestra como podria evolucionar la volatilidad en el corto plazo.",
        "estadistico": "Pronostico de varianza o volatilidad condicional derivado del modelo ARCH/GARCH/EGARCH ajustado.",
    },
    "regression_scatter": {
        "general": "Compara el comportamiento del activo frente al benchmark.",
        "estadistico": "Diagrama de dispersion activo vs benchmark con pendiente asociada al beta del CAPM.",
    },
    "benchmark_comparison": {
        "general": "Permite ver si el portafolio le gana o pierde al indice de referencia.",
        "estadistico": "Comparacion de desempeno relativo usando retorno, drawdown, alpha, tracking error e information ratio.",
    },
    "jarque_bera": {
        "general": "Prueba si la forma de la distribucion se aleja de la normal.",
        "estadistico": "Contrasta normalidad usando asimetria y curtosis; p-value bajo sugiere rechazo de normalidad.",
    },
    "shapiro_wilk": {
        "general": "Prueba si los datos se parecen a una distribucion normal.",
        "estadistico": "Test de normalidad sensible a desviaciones respecto a la gaussiana, especialmente en muestras pequenas y medianas.",
    },
    "anderson_darling": {
        "general": "Evalua si los datos se apartan de la normalidad, dando mas peso a las colas.",
        "estadistico": "Prueba de ajuste que compara la distribucion empirica contra una normal, enfatizando discrepancias en extremos.",
    },
    "stochastic": {
        "general": "Ayuda a detectar si el precio esta cerca de extremos recientes.",
        "estadistico": "Oscilador basado en la posicion del cierre frente al rango maximo-minimo de una ventana.",
    },
    "moving_average_cross": {
        "general": "Se activa cuando dos medias moviles se cruzan y puede sugerir cambio de tendencia.",
        "estadistico": "Cruce entre medias de distinta sensibilidad usado como regla de señal alcista o bajista.",
    },
    "arch_model": {
        "general": "Modelo para captar cambios en la volatilidad a partir de choques recientes.",
        "estadistico": "ARCH modela la varianza condicional usando rezagos de errores al cuadrado.",
    },
    "garch_model": {
        "general": "Modelo que describe como cambia la volatilidad con el tiempo.",
        "estadistico": "GARCH modela la varianza condicional con rezagos de errores y de la propia varianza.",
    },
    "egarch_model": {
        "general": "Modelo de volatilidad que puede capturar reacciones diferentes a noticias buenas y malas.",
        "estadistico": "EGARCH modela el logaritmo de la varianza y permite asimetria o efecto apalancamiento.",
    },
    "aic_bic": {
        "general": "Sirven para comparar modelos y elegir el mas conveniente.",
        "estadistico": "Criterios de informacion que balancean ajuste y complejidad; menor valor suele indicar mejor modelo.",
    },
    "conditional_volatility": {
        "general": "Es la volatilidad estimada para cada momento, no una unica volatilidad fija.",
        "estadistico": "Serie temporal de la desviacion estandar condicional estimada por un modelo de heterocedasticidad.",
    },
    "residual_normality": {
        "general": "Revisa si los residuos del modelo se comportan de forma razonable.",
        "estadistico": "Diagnostico sobre residuos o residuos estandarizados para evaluar especificacion y colas remanentes.",
    },
        "simple_return": {
        "general": "Muestra el cambio porcentual de un periodo a otro.",
        "estadistico": "Retorno simple = (P_t / P_{t-1}) - 1.",
    },
    "log_return": {
        "general": "Es otra forma de medir el cambio del precio, muy usada en finanzas y modelos estadisticos.",
        "estadistico": "Retorno logaritmico = ln(P_t / P_{t-1}); es aditivo en el tiempo y util en modelacion.",
    },
}