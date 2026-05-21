from __future__ import annotations

COURSE_RISK_NOTES = [
    {
        "keywords": ["dashboard", "tablero", "proyecto", "aplicacion", "aplicación"],
        "note": (
            "El dashboard integra selección de portafolio, retorno, riesgo, benchmark, modelos estadísticos, "
            "stress testing, ML y reporte para sustentar una decisión financiera completa."
        ),
    },
    {
        "keywords": ["horizonte", "plazo", "tiempo"],
        "note": (
            "El horizonte cambia la muestra y la acumulación del riesgo: a mayor plazo se observa más exposición "
            "a volatilidad, pérdidas extremas y sensibilidad frente al mercado."
        ),
    },
    {
        "keywords": ["var", "cvar", "perdida", "pérdida", "kupiec"],
        "note": (
            "VaR resume una pérdida máxima esperada bajo confianza e intervalo; CVaR complementa con severidad "
            "promedio de la cola, y Kupiec evalúa si la frecuencia de excepciones del VaR es razonable."
        ),
    },
    {
        "keywords": ["capm", "beta", "alpha", "alfa", "jensen"],
        "note": (
            "CAPM conecta retorno esperado con beta de mercado; beta mayor a 1 implica más sensibilidad y alpha "
            "positivo sugiere desempeño superior ajustado por riesgo."
        ),
    },
    {
        "keywords": ["garch", "arch", "egarch", "volatilidad"],
        "note": (
            "Los modelos ARCH/GARCH describen agrupamiento de volatilidad: periodos turbulentos tienden a seguir "
            "a periodos turbulentos, por eso sirven para estimar riesgo condicional."
        ),
    },
    {
        "keywords": ["markowitz", "frontera", "sharpe", "optimización", "optimizacion"],
        "note": (
            "Markowitz busca combinaciones eficientes de retorno y volatilidad; la frontera eficiente permite "
            "comparar portafolios y seleccionar pesos coherentes con el perfil de riesgo."
        ),
    },
    {
        "keywords": ["stress", "estres", "estrés", "escenario", "shock"],
        "note": (
            "Stress testing no pronostica el futuro: aplica shocks adversos para medir resiliencia, pérdida "
            "potencial y comportamiento relativo frente al benchmark."
        ),
    },
    {
        "keywords": ["machine learning", "ml", "modelo", "prediccion", "predicción"],
        "note": (
            "El ML se usa como complemento predictivo, no causal; ayuda a estimar retorno acumulado con variables "
            "financieras como volatilidad, Sharpe, VaR, beta, mercado y horizonte."
        ),
    },
]


def find_course_notes(question: str, limit: int = 2) -> list[str]:
    normalized = question.lower()
    matches: list[tuple[int, str]] = []
    for item in COURSE_RISK_NOTES:
        score = sum(1 for keyword in item["keywords"] if keyword in normalized)
        if score:
            matches.append((score, item["note"]))
    matches.sort(key=lambda item: item[0], reverse=True)
    return [note for _, note in matches[:limit]]
