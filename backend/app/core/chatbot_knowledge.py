from __future__ import annotations

CHATBOT_KNOWLEDGE_BASE = {
    "var": {
        "keywords": ["var", "value at risk", "valor en riesgo", "riesgo extremo", "percentil", "cuantil"],
        "title": "VaR / Value at Risk",
        "source_type": "teoria",
        "reference": "Proyecto Integrador Riesgo USTA: modulo VaR, CVaR y backtesting Kupiec.",
        "general": (
            "El VaR estima la perdida maxima esperada de un portafolio para un horizonte y un nivel de confianza. "
            "Por ejemplo, un VaR diario al 95% indica que, bajo el modelo usado, el 5% de los dias podrian presentar "
            "perdidas superiores a ese umbral. En el proyecto se trabaja con VaR parametrico, historico y Monte Carlo."
        ),
        "estadistico": (
            "Estadisticamente, el VaR es un cuantil de la distribucion de perdidas o de rendimientos negativos. "
            "El metodo parametrico depende de supuestos distribucionales, el historico usa percentiles empiricos y "
            "Monte Carlo simula escenarios para estimar la cola de perdidas."
        ),
        "followups": [
            "Cual es la diferencia entre VaR historico, parametrico y Monte Carlo?",
            "Como se interpreta un VaR al 95%?",
            "Como se valida el VaR con Kupiec?",
        ],
    },
    "cvar": {
        "keywords": ["cvar", "expected shortfall", "cola", "perdida esperada", "p?rdida esperada", "riesgo de cola"],
        "title": "CVaR / Expected Shortfall",
        "source_type": "teoria",
        "reference": "Proyecto Integrador Riesgo USTA: CVaR como medida complementaria de riesgo de cola.",
        "general": (
            "El CVaR mide la perdida promedio en los peores escenarios, es decir, cuando la perdida ya supero el VaR. "
            "Por eso complementa al VaR: no solo marca un umbral, sino que estima que tan severas pueden ser las perdidas "
            "dentro de la cola."
        ),
        "estadistico": (
            "El CVaR es una esperanza condicional sobre la cola de la distribucion. Si el VaR identifica el cuantil critico, "
            "el CVaR promedia las observaciones o simulaciones que quedan mas alla de ese cuantil. Esto lo hace mas informativo "
            "cuando existen colas pesadas o eventos extremos."
        ),
        "followups": [
            "Por que CVaR puede ser mas conservador que VaR?",
            "Como se interpreta el CVaR en una grafica de perdidas?",
            "Que diferencia hay entre riesgo de umbral y riesgo de cola?",
        ],
    },
    "kupiec": {
        "keywords": ["kupiec", "backtesting", "excedencias", "violaciones", "lr_pof", "proportion of failures"],
        "title": "Backtesting de Kupiec",
        "source_type": "teoria",
        "reference": "Proyecto Integrador Riesgo USTA: test de Kupiec para validar la proporcion de fallas del VaR.",
        "general": (
            "El test de Kupiec valida si la cantidad de veces que las perdidas reales superan el VaR es coherente con "
            "el nivel de confianza elegido. Si hay demasiadas excedencias, el modelo puede estar subestimando el riesgo; "
            "si hay muy pocas, puede estar siendo demasiado conservador."
        ),
        "estadistico": (
            "Kupiec, o prueba de proporcion de fallas, compara la tasa observada de violaciones contra la tasa esperada. "
            "Para un VaR al 95%, se espera aproximadamente un 5% de excedencias. El estadistico LR_POF se compara contra "
            "una distribucion chi-cuadrado con 1 grado de libertad."
        ),
        "followups": [
            "Que significa que el test de Kupiec rechace el VaR?",
            "Cuando un VaR subestima el riesgo?",
            "Por que conviene aplicar Kupiec a varios metodos de VaR?",
        ],
    },
    "capm": {
        "keywords": [
            "capm",
            "beta",
            "alpha",
            "alfa",
            "r2",
            "r cuadrado",
            "retorno esperado",
            "mercado",
            "benchmark",
            "tasa libre de riesgo",
        ],
        "title": "CAPM",
        "source_type": "modulo",
        "reference": "Proyecto Integrador Riesgo USTA: modulo CAPM por activo y por portafolio.",
        "general": (
            "El CAPM explica el retorno esperado de un activo o portafolio a partir de su exposicion al mercado. "
            "La beta mide sensibilidad frente al benchmark: una beta menor que 1 suele indicar comportamiento defensivo, "
            "una beta cercana a 1 indica comportamiento similar al mercado y una beta mayor que 1 indica mayor agresividad. "
            "El alpha permite evaluar si el activo o portafolio obtuvo un rendimiento adicional frente a lo esperado por el modelo."
        ),
        "estadistico": (
            "Estadisticamente, CAPM estima beta como la covarianza entre los rendimientos del activo y del benchmark dividida "
            "por la varianza del benchmark. El modelo tambien calcula alpha, R2 y retorno esperado usando la tasa libre de riesgo "
            "y la prima de mercado. En el proyecto se usa para analizar activos individuales y portafolios."
        ),
        "followups": [
            "Como se interpreta una beta mayor que 1?",
            "Que significa un alpha positivo en CAPM?",
            "Para que sirve el R2 en una regresion CAPM?",
        ],
    },
    "markowitz": {
        "keywords": ["markowitz", "frontera eficiente", "sharpe", "mínima varianza", "minima varianza", "portafolio"],
        "title": "Markowitz y frontera eficiente",
        "source_type": "modulo",
        "reference": "Backend PortfolioService: frontera eficiente, mínimo riesgo y máximo Sharpe.",
        "general": (
            "Markowitz busca construir portafolios eficientes combinando retorno esperado, volatilidad y diversificación. "
            "La frontera eficiente muestra combinaciones donde no se puede obtener más retorno sin asumir más riesgo."
        ),
        "estadistico": (
            "El módulo usa rendimientos históricos para estimar medias, matriz de covarianzas y correlaciones. "
            "Con esa información simula portafolios y optimiza mínima varianza y máximo Sharpe."
        ),
        "followups": [
            "¿Qué significa estar sobre la frontera eficiente?",
            "¿Por qué la diversificación reduce riesgo?",
        ],
    },
    "garch": {
        "keywords": ["garch", "arch", "egarch", "volatilidad condicional", "heterocedasticidad"],
        "title": "ARCH / GARCH / EGARCH",
        "source_type": "modulo",
        "reference": "Backend GarchService: comparación ARCH, GARCH y EGARCH por AIC/BIC.",
        "general": (
            "Los modelos ARCH/GARCH permiten modelar volatilidad cambiante en el tiempo. "
            "Son útiles cuando los rendimientos presentan periodos de alta y baja volatilidad agrupada."
        ),
        "estadistico": (
            "El backend compara ARCH(1), GARCH(1,1) y EGARCH(1,1), selecciona el mejor modelo por AIC "
            "y reporta diagnóstico de residuos y pronóstico de volatilidad."
        ),
        "followups": [
            "¿Por qué se usa GARCH en series financieras?",
            "¿Qué significa volatilidad condicional?",
        ],
    },
    "perri": {
        "keywords": ["perri", "umbrales", "institucional", "5 activos", "10 activos", "15 activos"],
        "title": "Perri institucional",
        "source_type": "metodologia",
        "reference": "Backend PerriOptimizerService: portafolios exactos por tamaño, horizonte y objetivo.",
        "general": (
            "Perri es la referencia institucional del proyecto. Calcula portafolios exactos de 5, 10 y 15 activos "
            "para horizontes de 1, 3 y 5 años, usando objetivos de mínimo riesgo, máximo Sharpe y máxima rentabilidad."
        ),
        "estadistico": (
            "Perri usa precios persistidos en SQLite, construye retornos por horizonte, selecciona candidatos "
            "y optimiza pesos bajo restricciones de suma, peso mínimo y peso máximo por activo."
        ),
        "followups": [
            "¿Cómo se compara Markowitz contra Perri?",
            "¿Qué significa selección exacta en Perri?",
        ],
    },
    "black_scholes": {
        "keywords": ["black-scholes", "black scholes", "opción", "opciones", "call", "put", "griegas"],
        "title": "Black-Scholes",
        "source_type": "modulo",
        "reference": "Backend OptionService: valoración de opciones y griegas.",
        "general": (
            "Black-Scholes permite valorar opciones financieras tipo call o put usando precio spot, strike, "
            "tiempo al vencimiento, tasa libre de riesgo y volatilidad."
        ),
        "estadistico": (
            "El modelo calcula el precio teórico de la opción y griegas como delta, gamma y vega, "
            "que miden sensibilidad del precio frente a cambios en el activo subyacente y la volatilidad."
        ),
        "followups": [
            "¿Qué mide delta en Black-Scholes?",
            "¿Qué representa vega en una opción?",
        ],
    },
    "nelson_siegel": {
        "keywords": ["nelson", "siegel", "curva de tasas", "yield curve", "tasas"],
        "title": "Nelson-Siegel",
        "source_type": "modulo",
        "reference": "Backend YieldService: ajuste de curva de tasas.",
        "general": (
            "Nelson-Siegel modela la curva de tasas usando componentes de nivel, pendiente y curvatura. "
            "Sirve para representar la estructura temporal de tasas de interés."
        ),
        "estadistico": (
            "El backend ajusta los parámetros tau, beta0, beta1 y beta2 minimizando el error cuadrático "
            "entre tasas observadas y tasas estimadas por la curva."
        ),
        "followups": [
            "¿Qué significa beta0 en Nelson-Siegel?",
            "¿Para qué sirve modelar la curva de tasas?",
        ],
    },
}
