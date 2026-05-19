from __future__ import annotations

import re

from app.clients.llm_client import LLMClient


class ChatbotService:
    """
    Servicio base del chatbot experto en teoría del riesgo.

    Esta versión:
    - Mantiene motor experto local como fallback seguro.
    - Recibe LLMClient por inyección de dependencias.
    - Solo usa IA real si LLMClient está habilitado y retorna respuesta.
    - Evita llamadas externas cuando LLM_PROVIDER=local.
    """

    KNOWLEDGE_BASE = {
        "var": {
            "keywords": ["var", "value at risk", "valor en riesgo", "riesgo extremo"],
            "title": "VaR / Value at Risk",
            "source_type": "teoria",
            "reference": "Teoría del riesgo: medición de pérdidas potenciales bajo un nivel de confianza.",
            "general": (
                "El VaR estima la pérdida máxima esperada de un portafolio durante un horizonte determinado "
                "y con un nivel de confianza específico. Por ejemplo, un VaR al 95% indica que, bajo las "
                "condiciones del modelo, solo el 5% de los escenarios deberían superar esa pérdida."
            ),
            "estadistico": (
                "Estadísticamente, el VaR corresponde a un cuantil de la distribución de pérdidas. "
                "En el proyecto se calcula por métodos histórico, paramétrico y Monte Carlo, lo que permite "
                "comparar supuestos empíricos, distribucionales y simulados."
            ),
            "followups": [
                "¿Cómo se interpreta el VaR histórico?",
                "¿Cuál es la diferencia entre VaR y CVaR?",
            ],
        },
        "cvar": {
            "keywords": ["cvar", "expected shortfall", "cola", "pérdida esperada"],
            "title": "CVaR / Expected Shortfall",
            "source_type": "teoria",
            "reference": "Teoría del riesgo: pérdida esperada condicional en la cola.",
            "general": (
                "El CVaR mide la pérdida promedio cuando ya se superó el umbral del VaR. "
                "Es útil porque no solo indica un punto crítico, sino la severidad esperada en los peores escenarios."
            ),
            "estadistico": (
                "El CVaR es una esperanza condicional sobre la cola de la distribución de pérdidas. "
                "A diferencia del VaR, incorpora la magnitud de las pérdidas extremas más allá del cuantil."
            ),
            "followups": [
                "¿Por qué CVaR puede ser más conservador que VaR?",
                "¿Cómo se usa CVaR en gestión de portafolios?",
            ],
        },
        "capm": {
            "keywords": ["capm", "beta", "alpha", "alfa", "retorno esperado", "mercado"],
            "title": "CAPM",
            "source_type": "modulo",
            "reference": "Backend CAPM: beta, alpha, retorno esperado y R².",
            "general": (
                "El CAPM relaciona el retorno esperado de un activo con su exposición al mercado. "
                "La beta mide sensibilidad frente al benchmark: menor que 1 suele indicar comportamiento defensivo, "
                "cercana a 1 comportamiento similar al mercado y mayor que 1 mayor agresividad."
            ),
            "estadistico": (
                "En el proyecto, CAPM estima beta mediante covarianza entre el activo y el benchmark dividida "
                "por la varianza del benchmark. También calcula alpha, R² y retorno esperado usando tasa libre de riesgo."
            ),
            "followups": [
                "¿Cómo se interpreta una beta mayor que 1?",
                "¿Qué significa alpha positivo en CAPM?",
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

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client

    def _normalize(self, text: str) -> str:
        value = text.strip().lower()
        value = re.sub(r"\s+", " ", value)
        return value

    def _detect_topics(self, question: str, module: str | None = None) -> list[str]:
        normalized = self._normalize(question)

        detected = []

        if module and module in self.KNOWLEDGE_BASE:
            detected.append(module)

        for topic, payload in self.KNOWLEDGE_BASE.items():
            keywords = payload["keywords"]
            if any(keyword in normalized for keyword in keywords):
                if topic not in detected:
                    detected.append(topic)

        return detected

    def _build_llm_context(self, topic: str, payload: dict, local_answer: str) -> str:
        return (
            f"Tema detectado: {topic}\n"
            f"Fuente interna: {payload['title']}\n"
            f"Tipo de fuente: {payload['source_type']}\n"
            f"Referencia: {payload['reference']}\n"
            f"Respuesta base local: {local_answer}"
        )

    def answer_question(
        self,
        question: str,
        mode: str = "general",
        module: str | None = None,
    ) -> dict:
        normalized_question = question.strip()
        normalized_mode = mode.strip().lower()
        normalized_module = module.strip().lower() if module else None

        topics = self._detect_topics(
            question=normalized_question,
            module=normalized_module,
        )

        if not topics:
            return {
                "question": normalized_question,
                "mode": normalized_mode,
                "module": normalized_module,
                "supported": False,
                "answer": (
                    "No encontré soporte suficiente en la base de conocimiento local del proyecto para responder "
                    "esa pregunta con seguridad. Reformula la pregunta usando un módulo como VaR, CVaR, CAPM, "
                    "Markowitz, GARCH, Perri, Nelson-Siegel o Black-Scholes."
                ),
                "topics": [],
                "sources": [],
                "suggested_followups": [
                    "¿Qué es el VaR?",
                    "¿Cómo se interpreta CAPM?",
                    "¿Qué hace Perri en el proyecto?",
                ],
            }

        selected_topic = topics[0]
        payload = self.KNOWLEDGE_BASE[selected_topic]

        local_answer = payload["estadistico"] if normalized_mode == "estadistico" else payload["general"]
        answer = local_answer

        if self.llm_client is not None:
            context = self._build_llm_context(
                topic=selected_topic,
                payload=payload,
                local_answer=local_answer,
            )
            llm_answer = self.llm_client.generate_answer(
                question=normalized_question,
                context=context,
                mode=normalized_mode,
            )

            if llm_answer:
                answer = llm_answer

        sources = [
            {
                "title": payload["title"],
                "source_type": payload["source_type"],
                "reference": payload["reference"],
            }
        ]

        return {
            "question": normalized_question,
            "mode": normalized_mode,
            "module": normalized_module,
            "supported": True,
            "answer": answer,
            "topics": topics,
            "sources": sources,
            "suggested_followups": payload["followups"],
        }
