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
        "keywords": [
            "markowitz",
            "frontera eficiente",
            "sharpe",
            "minima varianza",
            "m?nima varianza",
            "maximo sharpe",
            "m?ximo sharpe",
            "portafolio",
            "covarianza",
            "correlacion",
            "correlaci?n",
            "diversificacion",
            "diversificaci?n",
        ],
        "title": "Markowitz y frontera eficiente",
        "source_type": "modulo",
        "reference": "Proyecto Integrador Riesgo USTA: modulo PortfolioService y frontera eficiente.",
        "general": (
            "Markowitz permite construir portafolios eficientes combinando retorno esperado, volatilidad y diversificacion. "
            "La frontera eficiente muestra portafolios donde no se puede aumentar retorno sin asumir mas riesgo. "
            "En el proyecto se identifican portafolios como minima varianza, maximo Sharpe, portafolio objetivo y portafolio sugerido por perfil."
        ),
        "estadistico": (
            "Estadisticamente, Markowitz usa rendimientos historicos para estimar medias, volatilidades, matriz de covarianzas "
            "y matriz de correlaciones. Con esos insumos simula portafolios y optimiza pesos bajo restricciones. "
            "El Sharpe compara exceso de retorno frente a la tasa libre de riesgo por unidad de volatilidad."
        ),
        "followups": [
            "Que significa estar sobre la frontera eficiente?",
            "Por que la diversificacion reduce riesgo?",
            "Como se compara Markowitz contra Perri?",
        ],
    },
    "garch": {
        "keywords": [
            "garch",
            "arch",
            "egarch",
            "volatilidad condicional",
            "heterocedasticidad",
            "aic",
            "bic",
            "residuos",
            "pronostico",
            "pron?stico",
        ],
        "title": "ARCH / GARCH / EGARCH",
        "source_type": "modulo",
        "reference": "Proyecto Integrador Riesgo USTA: modulo GarchService para volatilidad condicional.",
        "general": (
            "Los modelos ARCH, GARCH y EGARCH sirven para estudiar volatilidad financiera cambiante en el tiempo. "
            "Son utiles cuando los rendimientos presentan agrupamientos de volatilidad: periodos tranquilos seguidos de periodos turbulentos. "
            "En el proyecto se usan para diagnosticar y pronosticar volatilidad condicional."
        ),
        "estadistico": (
            "Estadisticamente, GARCH modela la varianza condicional como funcion de choques pasados y volatilidad pasada. "
            "El backend compara ARCH, GARCH y EGARCH usando criterios como AIC y BIC, revisa diagnosticos de residuos "
            "y genera pronosticos de volatilidad."
        ),
        "followups": [
            "Por que se usa GARCH en series financieras?",
            "Que significa volatilidad condicional?",
            "Como se interpreta AIC y BIC en GARCH?",
        ],
    },
    "perri": {
        "keywords": [
            "perri",
            "umbrales",
            "institucional",
            "5 activos",
            "10 activos",
            "15 activos",
            "1y",
            "3y",
            "5y",
            "min_risk",
            "max_sharpe",
            "max_return",
            "seleccion exacta",
            "selecci?n exacta",
        ],
        "title": "Perri institucional",
        "source_type": "metodologia",
        "reference": "Proyecto Integrador Riesgo USTA: PerriOptimizerService y JSON precalculado institucional.",
        "general": (
            "Perri es la referencia institucional del proyecto para comparar portafolios. "
            "Calcula portafolios exactos de 5, 10 y 15 activos para horizontes de 1, 3 y 5 anos. "
            "Sus objetivos son minimo riesgo, maximo Sharpe y maxima rentabilidad, representados como min_risk, max_sharpe y max_return."
        ),
        "estadistico": (
            "Perri usa precios persistidos en SQLite, construye retornos por horizonte, selecciona candidatos y optimiza pesos. "
            "La comparacion Markowitz contra Perri permite revisar si el portafolio del usuario supera o no los umbrales institucionales "
            "en retorno, volatilidad y Sharpe para el mismo tamano y horizonte."
        ),
        "followups": [
            "Como se compara Markowitz contra Perri?",
            "Que significa seleccion exacta en Perri?",
            "Que representan min_risk, max_sharpe y max_return?",
        ],
    },
    "black_scholes": {
        "keywords": [
            "black-scholes",
            "black scholes",
            "opcion",
            "opci?n",
            "opciones",
            "call",
            "put",
            "griegas",
            "delta",
            "gamma",
            "vega",
            "theta",
            "rho",
            "strike",
            "volatilidad implicita",
            "volatilidad impl?cita",
        ],
        "title": "Black-Scholes",
        "source_type": "modulo",
        "reference": "Proyecto Integrador Riesgo USTA: OptionService para valoracion de opciones y griegas.",
        "general": (
            "Black-Scholes es un modelo usado para valorar opciones financieras tipo call y put. "
            "Utiliza variables como precio spot del activo, precio de ejercicio o strike, tiempo al vencimiento, "
            "tasa libre de riesgo y volatilidad. En el proyecto se usa para calcular precio teorico de opciones "
            "y sensibilidades conocidas como griegas."
        ),
        "estadistico": (
            "Estadisticamente, Black-Scholes asume un comportamiento lognormal del precio del subyacente y usa "
            "la distribucion normal acumulada para estimar el valor teorico de una opcion europea. "
            "Las griegas miden sensibilidad: delta frente al precio del subyacente, gamma frente al cambio de delta, "
            "vega frente a volatilidad, theta frente al paso del tiempo y rho frente a la tasa de interes."
        ),
        "followups": [
            "Que significa delta en Black-Scholes?",
            "Que mide vega en una opcion?",
            "Cual es la diferencia entre una opcion call y una put?",
        ],
    },
    "nelson_siegel": {
        "keywords": [
            "nelson",
            "siegel",
            "nelson-siegel",
            "curva de tasas",
            "yield curve",
            "tasas",
            "estructura temporal",
            "beta0",
            "beta1",
            "beta2",
            "tau",
            "nivel",
            "pendiente",
            "curvatura",
        ],
        "title": "Nelson-Siegel",
        "source_type": "modulo",
        "reference": "Proyecto Integrador Riesgo USTA: YieldService para ajuste de curva de tasas.",
        "general": (
            "Nelson-Siegel es un modelo para representar la curva de tasas de interes a diferentes vencimientos. "
            "Resume la estructura temporal mediante componentes de nivel, pendiente y curvatura. "
            "En el proyecto se usa para ajustar una curva teorica a tasas observadas por vencimiento."
        ),
        "estadistico": (
            "El modelo estima parametros beta0, beta1, beta2 y tau. beta0 representa el nivel de largo plazo, "
            "beta1 captura la pendiente de corto plazo, beta2 representa la curvatura y tau controla la velocidad "
            "de decaimiento de los factores. El ajuste busca minimizar el error entre tasas observadas y tasas estimadas."
        ),
        "followups": [
            "Que representa beta0 en Nelson-Siegel?",
            "Para que sirve modelar la curva de tasas?",
            "Que significan nivel, pendiente y curvatura?",
        ],
    },


    "kyc": {
        "keywords": [
            "kyc",
            "perfil de riesgo",
            "inversionista",
            "horizonte",
            "preferencias",
            "conservador",
            "moderado",
            "agresivo",
            "tolerancia al riesgo"
        ],
        "title": "KYC y perfil del inversionista",
        "source_type": "modulo",
        "reference": "Proyecto Integrador Riesgo USTA: modulo InvestorService.",
        "general": (
            "El KYC financiero permite identificar el perfil del inversionista antes de recomendar un portafolio. "
            "En el proyecto se consideran perfiles conservador, moderado y agresivo junto con horizonte y tolerancia al riesgo."
        ),
        "estadistico": (
            "Metodologicamente, el perfil del inversionista condiciona la interpretacion de volatilidad, VaR, CVaR, drawdown y asignacion de pesos. "
            "Perfiles conservadores priorizan menor volatilidad y perfiles agresivos aceptan mayor dispersion."
        ),
        "followups": [
            "Que diferencia hay entre perfil conservador y agresivo?",
            "Como afecta el horizonte al riesgo?",
            "Como se conecta KYC con Markowitz?"
        ],
    },

    "roboadvisor": {
        "keywords": [
            "roboadvisor",
            "asesor automatico",
            "portafolio sugerido",
            "perfil conservador",
            "perfil moderado",
            "perfil agresivo",
            "recomendacion automatizada"
        ],
        "title": "RoboAdvisor",
        "source_type": "modulo",
        "reference": "Proyecto Integrador Riesgo USTA: modulo RoboAdvisorService.",
        "general": (
            "El RoboAdvisor genera recomendaciones automatizadas de portafolios segun perfil de riesgo y activos disponibles. "
            "En el proyecto considera perfiles como conservador, moderado y agresivo para orientar la sugerencia."
        ),
        "estadistico": (
            "El RoboAdvisor combina perfilamiento financiero y optimizacion de portafolios. "
            "Las recomendaciones deben validarse con metricas como Sharpe, VaR, CVaR y drawdown."
        ),
        "followups": [
            "Como usa el RoboAdvisor el perfil de riesgo?",
            "Que metricas validan una recomendacion automatizada?",
            "Cual es la diferencia entre RoboAdvisor y Perri?"
        ],
    },

}