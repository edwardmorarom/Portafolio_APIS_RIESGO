from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from ui.page_setup import setup_dashboard_page
from ui.asset_metadata import display_country
from ui.dashboard_ui import (
    header_dashboard,
    nota,
    seccion,
    titulo_con_ayuda,
    tarjeta_kpi,
)
from ui.cards import render_chip_row, render_info_card, render_meta_row
from ui.theme import image_to_base64, safe_text
from ui.portfolio_state import active_benchmark_details
from services.api_client import get_api_client, ApiClientError



CONTEXT_MODULE_GROUPS = {
    "Mercado y contexto": [
        {"code": "Módulo 0", "title": "Contextualización", "description": "Universo de activos, moneda, Rf y benchmark.", "path": "pages/0_Contextualizacion.py"},
        {"code": "Módulo 1", "title": "Técnico", "description": "Precio, medias móviles, RSI, Bollinger, MACD y estocástico.", "path": "pages/01_Tecnico.py"},
        {"code": "Módulo 2", "title": "Rendimientos", "description": "Distribución, normalidad, QQ plot y estadística descriptiva.", "path": "pages/02_Rendimientos.py"},
        {"code": "Módulo 8", "title": "Macro y benchmark", "description": "Tasa libre de riesgo, FX, alpha, tracking error e IR.", "path": "pages/08_Macro_Benchmark.py"},
    ],
    "Riesgo cuantitativo": [
        {"code": "Módulo 3", "title": "GARCH", "description": "ARCH, GARCH, EGARCH, diagnóstico y pronóstico de volatilidad.", "path": "pages/03_Garch.py"},
        {"code": "Módulo 4", "title": "CAPM", "description": "Beta, alpha, retorno esperado y lectura por activo o portafolio.", "path": "pages/04_Capm.py"},
        {"code": "Módulo 5", "title": "VaR/CVaR", "description": "VaR histórico, paramétrico, Monte Carlo, CVaR y Kupiec.", "path": "pages/05_Var_Cvar.py"},
        {"code": "Módulo 11", "title": "Stress testing", "description": "Escenarios adversos de tasa, mercado y volatilidad.", "path": "pages/11_Stress_Testing.py"},
    ],
    "Optimización y modelos": [
        {"code": "Módulo 6", "title": "Markowitz", "description": "Frontera eficiente, mínimos, Sharpe y comparación Perri.", "path": "pages/06_Markowitz.py"},
        {"code": "Módulo 7", "title": "Señales", "description": "Lectura integrada de señales técnicas por activo.", "path": "pages/07_Señales.py"},
        {"code": "Módulo 9", "title": "Renta fija", "description": "Nelson-Siegel, curva de tasas, duración y convexidad.", "path": "pages/09_Renta_Fija.py"},
        {"code": "Módulo 10", "title": "Opciones", "description": "Black-Scholes, Greeks, payoff y sensibilidad.", "path": "pages/10_Opciones.py"},
        {"code": "Módulo 12", "title": "Machine Learning", "description": "Predicción de retorno con variables de riesgo y mercado.", "path": "pages/12_Machine_Learning.py"},
    ],
}


LOGO_BY_TICKER = {
    "BP.L": "frontend/assets/logos/bp.png",
    "CA.PA": "frontend/assets/logos/carrefour.png",
    "ATD.TO": "frontend/assets/logos/couche_tard.png",
    "FEMSAUBD.MX": "frontend/assets/logos/femsa.png",
    "3382.T": "frontend/assets/logos/seven_i.png",
}


def _get_logo_path(ticker: str) -> str | None:
    path = LOGO_BY_TICKER.get((ticker or "").upper())
    if not path:
        return None
    return path if Path(path).exists() else None


def _build_asset_profile(name: str, ticker: str, country: str, is_default: bool) -> dict[str, str]:
    ticker_u = (ticker or "").upper()
    name_l = (name or "").lower()
    country_t = country or "N/D"

    if "bp" in name_l or ticker_u == "BP.L":
        return {
            "rol": "Cobertura sectorial",
            "aporte": "Exposición energética y sensibilidad macroeconómica.",
            "tesis": (
                "BP introduce un componente más cíclico en el portafolio. Su comportamiento puede reaccionar "
                "a shocks de energía, inflación, geopolítica y actividad global, por lo que aporta una fuente "
                "de riesgo distinta frente a activos ligados al consumo y retail."
            ),
            "riesgo": (
                "Riesgo relativamente alto por exposición a commodities, ciclo económico y eventos internacionales."
            ),
            "lectura": (
                "Aporta beta sectorial y fortalece la diversificación al no moverse igual que los activos más defensivos."
            ),
        }

    if "femsa" in name_l or ticker_u == "FEMSAUBD.MX":
        return {
            "rol": "Exposición regional",
            "aporte": "Latinoamérica, consumo y estructura operativa diversificada.",
            "tesis": (
                "FEMSA incorpora exposición a mercados emergentes y una dinámica distinta a la de Europa, Canadá o Japón. "
                "Eso permite capturar una mezcla entre estabilidad operativa y sensibilidad regional."
            ),
            "riesgo": (
                "Riesgo medio-alto por exposición cambiaria, entorno macro regional y sensibilidad a crecimiento de emergentes."
            ),
            "lectura": (
                "Aporta diversificación geográfica y una fuente de retorno diferente al resto del universo."
            ),
        }

    if "carrefour" in name_l or ticker_u == "CA.PA":
        return {
            "rol": "Retail defensivo",
            "aporte": "Consumo recurrente y comportamiento relativamente estable.",
            "tesis": (
                "Carrefour aporta una lectura más defensiva, asociada al consumo básico y a dinámicas menos volátiles "
                "que las de sectores más cíclicos. Dentro del portafolio ayuda a amortiguar parcialmente episodios de estrés."
            ),
            "riesgo": (
                "Riesgo medio, con sensibilidad a consumo europeo, márgenes operativos y entorno de tasas."
            ),
            "lectura": (
                "Funciona como activo estabilizador relativo frente a nombres con mayor exposición macro o sectorial."
            ),
        }

    if "couche" in name_l or ticker_u == "ATD.TO":
        return {
            "rol": "Retail resiliente",
            "aporte": "Negocio defensivo con operación internacional.",
            "tesis": (
                "Alimentation Couche-Tard agrega una exposición de consumo recurrente con una base operacional sólida. "
                "Su presencia mejora la mezcla entre estabilidad, escala y resiliencia dentro de un portafolio internacional."
            ),
            "riesgo": (
                "Riesgo medio, menor que activos energéticos o emergentes, aunque sensible a crecimiento y consumo."
            ),
            "lectura": (
                "Ayuda a construir una capa menos agresiva dentro del conjunto analizado."
            ),
        }

    if "seven" in name_l or ticker_u == "3382.T":
        return {
            "rol": "Consumo asiático",
            "aporte": "Exposición a Japón y retail con comportamiento diferencial.",
            "tesis": (
                "Seven & i Holdings incorpora exposición asiática y una fuente de riesgo distinta a América y Europa. "
                "Esto fortalece la diversificación internacional porque el activo no responde exactamente a los mismos impulsores que el resto."
            ),
            "riesgo": (
                "Riesgo medio, con sensibilidad a Japón, divisa y desempeño del retail asiático."
            ),
            "lectura": (
                "Sirve como componente de diversificación geográfica y reduce concentración regional del análisis."
            ),
        }

    if is_default:
        return {
            "rol": "Activo base del proyecto",
            "aporte": "Hace parte del núcleo inicial definido por el backend.",
            "tesis": (
                "Este activo pertenece al universo principal del proyecto y participa en la lógica de comparación, "
                "riesgo y optimización del tablero."
            ),
            "riesgo": "Su riesgo depende de su mercado, sector y benchmark de referencia.",
            "lectura": "Aporta al universo inicial del análisis y a la construcción del portafolio académico.",
        }

    return {
        "rol": "Activo complementario",
        "aporte": f"Amplía el universo internacional desde {country_t}.",
        "tesis": (
            "Se incorpora como activo adicional para enriquecer el universo de análisis y explorar perfiles de "
            "riesgo-retorno fuera del núcleo base."
        ),
        "riesgo": "Riesgo dependiente del país, sector y benchmark de referencia.",
        "lectura": "Permite ampliar escenarios de comparación y diversificación.",
    }


def _fetch_assets_and_help() -> tuple[list[dict], dict[str, dict[str, str]], str | None]:
    client = get_api_client()

    try:
        assets_payload = client.get_assets()
        assets = assets_payload.get("assets", [])
    except ApiClientError as exc:
        return [], {}, f"No fue posible cargar el universo de activos desde backend: {exc.message}"

    try:
        help_payload = client.get_help_catalog()
        help_items = help_payload.get("items", [])
        help_map = {item["key"]: item for item in help_items}
    except ApiClientError:
        help_map = {}

    return assets, help_map, None


def _chunks(items: list[dict], size: int) -> list[list[dict]]:
    return [items[i:i + size] for i in range(0, len(items), size)]



def _render_context_module_card(module: dict) -> None:
    st.markdown(
        f"""
        <div class="module-card">
            <div class="module-card-kicker">{safe_text(module["code"])}</div>
            <div class="module-card-title">{safe_text(module["title"])}</div>
            <div class="module-card-body">{safe_text(module["description"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link(
        module["path"],
        label=f"Abrir {module['title']}",
        use_container_width=True,
    )


def _render_context_modules_tab() -> None:
    group_tabs = st.tabs(list(CONTEXT_MODULE_GROUPS.keys()))

    for tab, (_, modules) in zip(group_tabs, CONTEXT_MODULE_GROUPS.items()):
        with tab:
            for row_start in range(0, len(modules), 2):
                cols = st.columns(2, gap="large")
                for col, module in zip(cols, modules[row_start:row_start + 2]):
                    with col:
                        _render_context_module_card(module)


def _render_context_status_tab() -> None:
    client = get_api_client()

    try:
        root = client.get_root()
        health = client.get_health()
        system = client.get("/system/status")

        c1, c2, c3 = st.columns(3)
        with c1:
            tarjeta_kpi("Backend", str(health.get("status", "N/D")).upper(), subtexto="FastAPI")
        with c2:
            tarjeta_kpi("Versin", str(root.get("version", system.get("app_version", "N/D"))), subtexto="API")
        with c3:
            tarjeta_kpi(
                "ML",
                "Activo" if system.get("ml_enabled") else "Inactivo",
                subtexto=system.get("ml_model_version", "N/D"),
            )

        render_meta_row(
            {
                "Entorno": health.get("env", "N/D"),
                "Prefijo API": system.get("api_prefix", "/api/v1"),
                "Chatbot": f"{system.get('chatbot_provider', 'local')}  {system.get('chatbot_model', 'N/D')}",
            }
        )
    except ApiClientError as exc:
        st.warning(f"No fue posible consultar el backend: {exc.message}")
    except Exception as exc:
        st.warning(f"No fue posible consultar el backend: {exc}")


def _render_analysis_center(modo: str) -> None:
    seccion("Centro de anlisis de portafolio")

    render_meta_row(
        {
            "Usuario": st.session_state.get("user_name", "N/D"),
            "Rol": "Superusuario" if st.session_state.get("user_role") == "superuser" else "Cliente",
            "Interfaz": "Diseo profesional",
            "Modo": modo,
        }
    )

    tab_home, tab_modules, tab_status = st.tabs(["Resumen", "Módulos", "Estado"])

    with tab_home:
        c1, c2, c3 = st.columns(3)
        with c1:
            tarjeta_kpi("Cobertura", "13", subtexto="Módulos Streamlit")
        with c2:
            tarjeta_kpi("Backend", "FastAPI", subtexto="Servicios financieros")
        with c3:
            tarjeta_kpi("Modelo", "ML", subtexto="Predicción de retorno")

        seccion("Flujo recomendado")
        cols = st.columns(3, gap="large")
        with cols[0]:
            render_info_card("1. Contexto", "Revisa activos, moneda, tasa libre de riesgo y benchmark.")
        with cols[1]:
            render_info_card("2. Riesgo", "Evala volatilidad, CAPM, VaR/CVaR, GARCH y stress testing.")
        with cols[2]:
            render_info_card("3. Decisin", "Contrasta Markowitz, señales, Perri, RoboAdvisor y ML.")

    with tab_modules:
        _render_context_modules_tab()

    with tab_status:
        _render_context_status_tab()


def _render_logo_card(ticker: str):
    logo_path = _get_logo_path(ticker)
    logo_b64 = image_to_base64(logo_path) if logo_path else ""

    if logo_b64:
        inner = (
            f'<img src="data:image/png;base64,{logo_b64}" '
            'style="max-width:92px; max-height:92px; width:auto; height:auto; object-fit:contain;" />'
        )
    else:
        inner = (
            f'<div style="font-size:1.05rem;font-weight:800;color:var(--accent-main);">'
            f'{safe_text(ticker)}</div>'
        )

    st.markdown(
        (
            '<div style="'
            'background:linear-gradient(180deg,#ffffff 0%, var(--panel-bg-2) 100%);'
            'border:1px solid var(--border-soft);'
            'border-radius:20px;'
            'box-shadow:var(--shadow-main);'
            'min-height:140px;'
            'display:flex;'
            'align-items:center;'
            'justify-content:center;'
            'padding:1rem;'
            'overflow:hidden;'
            '">'
            f'{inner}'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


def _render_role_card(profile: dict[str, str]):
    st.markdown(
        (
            '<div style="'
            'background:linear-gradient(180deg,#ffffff 0%, var(--panel-bg-2) 100%);'
            'border:1px solid var(--border-soft);'
            'border-radius:20px;'
            'box-shadow:var(--shadow-main);'
            'min-height:140px;'
            'padding:1rem 1.05rem;'
            'position:relative;'
            'overflow:hidden;'
            '">'
            '<div style="position:absolute;left:0;top:0;width:100%;height:4px;'
            'background:linear-gradient(90deg,var(--accent-main),var(--accent-second));"></div>'
            '<div style="font-size:0.80rem;font-weight:900;letter-spacing:0;'
            'text-transform:uppercase;color:var(--text-muted);margin-bottom:0.65rem;">'
            'Rol en portafolio'
            '</div>'
            f'<div style="font-size:1.45rem;font-weight:900;line-height:1.12;'
            f'color:var(--text-main);margin-bottom:0.55rem;">{safe_text(profile["rol"])}</div>'
            f'<div style="font-size:0.98rem;line-height:1.58;color:var(--text-soft);font-weight:600;">'
            f'{safe_text(profile["aporte"])}</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


def _render_financial_card(profile: dict[str, str], asset: dict):
    country = display_country(asset)
    base_tag = "Sí" if asset.get("default") else "No"
    asset_type = asset.get("asset_type") or "N/D"
    benchmark_ticker = asset.get("benchmark_ticker") or "N/D"
    benchmark_description = asset.get("benchmark_description") or "Benchmark no especificado"
    source = asset.get("source") or "N/D"

    st.markdown(
        (
            '<div style="'
            'background:linear-gradient(180deg,#ffffff 0%, var(--panel-bg-2) 100%);'
            'border:1px solid var(--border-soft);'
            'border-radius:20px;'
            'box-shadow:var(--shadow-main);'
            'min-height:140px;'
            'padding:1rem 1.1rem;'
            'overflow:hidden;'
            '">'
            '<div style="font-size:0.80rem;font-weight:900;letter-spacing:0;'
            'text-transform:uppercase;color:var(--text-muted);margin-bottom:0.7rem;">'
            'Lectura financiera del activo'
            '</div>'
            f'<div style="font-size:0.96rem;line-height:1.65;color:var(--text-soft);'
            f'font-weight:600;margin-bottom:0.85rem;">{safe_text(profile["tesis"])}</div>'
            '<div style="display:flex;flex-wrap:wrap;gap:0.45rem;margin-bottom:0.8rem;">'
            f'<span class="ui-chip"><strong>País:</strong>&nbsp;{safe_text(country)}</span>'
            f'<span class="ui-chip"><strong>Activo base:</strong>&nbsp;{base_tag}</span>'
            f'<span class="ui-chip"><strong>Clase:</strong>&nbsp;{safe_text(asset_type)}</span>'
            f'<span class="ui-chip"><strong>Benchmark:</strong>&nbsp;{safe_text(benchmark_ticker)}</span>'
            f'<span class="ui-chip"><strong>Fuente:</strong>&nbsp;{safe_text(source)}</span>'
            '</div>'
            f'<div style="font-size:0.92rem;line-height:1.58;color:var(--text-soft);font-weight:600;">'
            f'<strong>Riesgo:</strong> {safe_text(profile["riesgo"])}<br>'
            f'<strong>Benchmark metodológico:</strong> {safe_text(benchmark_description)}<br>'
            f'<strong>Lectura de portafolio:</strong> {safe_text(profile["lectura"])}'
            '</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )





def _render_asset_block(asset: dict, modo: str):
    profile = _build_asset_profile(
        name=asset.get("name", ""),
        ticker=asset.get("ticker", ""),
        country=display_country(asset),
        is_default=bool(asset.get("default")),
    )

    titulo_con_ayuda(
        f"{asset.get('name', 'Activo')} ({asset.get('ticker', 'N/D')})",
        "Resumen contextual y lectura financiera del activo dentro del universo del proyecto.",
        nivel=3,
    )

    render_chip_row(
        [
            f"País: {display_country(asset)}",
            f"Ticker: {asset.get('ticker', 'N/D')}",
            "Base del proyecto" if asset.get("default") else "Activo ampliado",
            f"Modo {modo}",
        ]
    )

    top_left, top_right = st.columns([0.9, 2.4], gap="large")

    with top_left:
        _render_logo_card(asset.get("ticker", ""))

    with top_right:
        _render_role_card(profile)

    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)

    _render_financial_card(profile, asset)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)


def _render_rf_and_benchmark_tab():
    seccion("Moneda base y conversión histórica a USD")


    render_info_card(
        "Nota metodológica sobre moneda",
        (
            "Los activos pueden cotizar en monedas distintas, pero el análisis se estandariza en USD. "
            "Así, rendimientos, CAPM, VaR/CVaR, GARCH y Markowitz quedan comparables."
        ),
    )

    conversion_rows = [
        {
            "Activo": "BP",
            "Ticker": "BP.L",
            "Moneda original": "GBP/GBp",
            "FX a USD": "GBPUSD=X",
            "Uso metodológico": "Conversión histórica a USD",
            "Nota": "Si el precio viene en pence, se corrige escala antes de convertir.",
        },
        {
            "Activo": "Carrefour",
            "Ticker": "CA.PA",
            "Moneda original": "EUR",
            "FX a USD": "EURUSD=X",
            "Uso metodológico": "Conversión histórica a USD",
            "Nota": "Permite comparar retornos en una moneda común.",
        },
        {
            "Activo": "Couche-Tard",
            "Ticker": "ATD.TO",
            "Moneda original": "CAD",
            "FX a USD": "CADUSD=X",
            "Uso metodológico": "Conversión histórica a USD",
            "Nota": "Evita mezclar retornos canadienses con retornos de otros mercados.",
        },
        {
            "Activo": "FEMSA",
            "Ticker": "FEMSAUBD.MX",
            "Moneda original": "MXN",
            "FX a USD": "MXNUSD=X",
            "Uso metodológico": "Conversión histórica a USD",
            "Nota": "Incorpora el efecto cambiario frente al dólar.",
        },
        {
            "Activo": "Seven & i",
            "Ticker": "3382.T",
            "Moneda original": "JPY",
            "FX a USD": "JPYUSD=X",
            "Uso metodológico": "Conversión histórica a USD",
            "Nota": "Permite integrar el activo japonés en el portafolio global.",
        },
    ]

    st.dataframe(pd.DataFrame(conversion_rows), use_container_width=True, hide_index=True)

    seccion("Tasa libre de riesgo")



    render_info_card(
        "Criterio usado para la Rf",
        (
            "Se usa una tasa libre de riesgo común en USD para mantener consistencia "
            "en Sharpe, CAPM y Markowitz."
        ),
    )

    rf_rows = [
        {
            "Concepto": "Rf principal del proyecto",
            "Ticker yfinance": "^IRX",
            "Descripción": "Treasury Bill USA 13 semanas",
            "Uso": "Tasa libre de riesgo común en USD para Sharpe, CAPM y Markowitz.",
        },
        {
            "Concepto": "Rf contextual USA 10Y",
            "Ticker yfinance": "^TNX",
            "Descripción": "Yield del Tesoro USA a 10 años",
            "Uso": "Referencia macro de largo plazo, no principal para Markowitz.",
        },
        {
            "Concepto": "Proxy Canadá",
            "Ticker yfinance": "CLF.TO",
            "Descripción": "ETF de bonos gubernamentales canadienses",
            "Uso": "Referencia contextual del mercado canadiense.",
        },
        {
            "Concepto": "Proxy México / emergentes",
            "Ticker yfinance": "EMB",
            "Descripción": "ETF de bonos de mercados emergentes",
            "Uso": "Referencia contextual para exposición emergente.",
        },
    ]

    st.dataframe(pd.DataFrame(rf_rows), use_container_width=True, hide_index=True)

    render_meta_row(
        [
            ("Rf principal", "^IRX"),
            ("Moneda base", "USD"),
            ("Uso", "Sharpe, CAPM y Markowitz"),
        ]
    )

    seccion("Benchmark del portafolio")
    benchmark_details = active_benchmark_details()



    render_info_card(
        f"Benchmark usado: {benchmark_details['ticker']}",
        (
            "ACWI funciona como referencia global porque el portafolio combina activos de varios países."
        ),
    )

    benchmark_rows = [
        {
            "Benchmark": benchmark_details["ticker"],
            "Nombre": benchmark_details.get("name", "Referencia"),
            "Criterio": benchmark_details.get("criterion", "N/D"),
            "Tipo": "Referencia global de renta variable",
            "Uso en el proyecto": "Comparación de desempeño, CAPM, beta, alpha de Jensen y métricas relativas.",
            "Justificación": "Es coherente con un portafolio internacional y multimoneda convertido a USD.",
        }
    ]

    st.dataframe(pd.DataFrame(benchmark_rows), use_container_width=True, hide_index=True)


    render_info_card(
        "Relación entre Rf, moneda y benchmark",
        (
            "USD, Rf en USD y ACWI alinean las métricas de riesgo y desempeño bajo el mismo marco metodológico."
        ),
    )


modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros De Contextualización",
    filtros_expanded=False,
)

assets, help_map, load_error = _fetch_assets_and_help()

view_mode = "Resumen"
selected_label = None
asset_map: dict[str, dict] = {}
show_general_read = False
show_default_only = False

header_dashboard(
    "Módulo 0 - Contextualización del portafolio",
    "Presenta el universo de activos, su lógica financiera, la conversión a USD, la tasa libre de riesgo y el benchmark global del proyecto",
    modo=modo,
)

if load_error:
    st.error(load_error)
    st.stop()

if modo == "General":
    nota(
        "Este módulo introduce el universo de activos definido por el backend y muestra por qué el portafolio combina geografías, sectores, monedas y perfiles de riesgo distintos."
    )
else:
    nota(
        "En modo estadístico, esta vista enfatiza que el portafolio no está concentrado en una sola región ni en una sola fuente de riesgo: mezcla activos con sensibilidades sectoriales, cambiarias y macroeconómicas diferentes."
    )

tab_activos, tab_rf_benchmark = st.tabs(
    ["Activos del portafolio", "Moneda, Rf y benchmark"]
)

with tab_activos:
    seccion("Resumen del universo")

    default_assets = [a for a in assets if a.get("default") is True]
    extra_assets = [a for a in assets if a.get("default") is not True]
    countries = sorted({display_country(a) for a in assets})

    perri_assets = [a for a in assets if a.get("include_in_perri") is True]

    by_asset_type: dict[str, int] = {}
    by_benchmark: dict[str, int] = {}

    for asset in assets:
        asset_type = asset.get("asset_type") or "sin_clasificar"
        benchmark = asset.get("benchmark_ticker") or "sin_benchmark"

        by_asset_type[asset_type] = by_asset_type.get(asset_type, 0) + 1
        by_benchmark[benchmark] = by_benchmark.get(benchmark, 0) + 1

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        tarjeta_kpi(
            "Activos disponibles",
            str(len(assets)),
            subtexto="Universo expuesto por el backend.",
            help_text="Cantidad de activos que llegan desde /api/v1/assets/.",
        )

    with c2:
        tarjeta_kpi(
            "Activos base",
            str(len(default_assets)),
            subtexto="Núcleo inicial del proyecto.",
            help_text="Activos marcados como default en el registro central.",
        )

    with c3:
        tarjeta_kpi(
            "Activos extra",
            str(len(extra_assets)),
            subtexto="Universo ampliado para explorar.",
            help_text="Activos adicionales habilitados para búsqueda o expansión.",
        )

    with c4:
        tarjeta_kpi(
            "Países cubiertos",
            str(len(countries)),
            subtexto="Diversificación geográfica observable.",
            help_text="Número de países representados en el universo actual.",
        )


    seccion("Marco metodológico del universo")

    metodologia_1, metodologia_2, metodologia_3, metodologia_4 = st.columns(4)

    with metodologia_1:
        tarjeta_kpi(
            "Benchmark global",
            "ACWI",
            subtexto="Referencia metodológica.",
            help_text="Benchmark global usado para comparar desempeño, CAPM, beta y alpha.",
        )

    with metodologia_2:
        tarjeta_kpi(
            "Moneda",
            "USD",
            subtexto="Base metodológica.",
            help_text="Todos los activos se trabajan en dólares para mantener comparabilidad.",
        )

    with metodologia_3:
        tarjeta_kpi(
            "Modo",
            modo,
            subtexto="Vista activa.",
            help_text="Modo de lectura usado en el tablero.",
        )

    with metodologia_4:
        tarjeta_kpi(
            "Fuente",
            "API",
            subtexto="Backend /assets.",
            help_text="Universo cargado desde el endpoint de activos del backend.",
        )

    seccion("Cobertura técnica para Perri")

    clases_txt = " · ".join([f"{k}: {v}" for k, v in sorted(by_asset_type.items())])
    benchmarks_txt = " · ".join([f"{k}: {v}" for k, v in sorted(by_benchmark.items())])

    perri_col, clases_col, benchmark_col = st.columns(3)

    with perri_col:
        tarjeta_kpi(
            "Activos Perri",
            str(len(perri_assets)),
            subtexto="Habilitados para RoboAdvisor.",
            help_text="Cantidad de activos disponibles para la lógica de Perri y portafolios recomendados.",
        )

    with clases_col:
        tarjeta_kpi(
            "Clases de activo",
            str(len(by_asset_type)),
            subtexto="Tipos representados.",
            help_text=clases_txt,
        )

    with benchmark_col:
        tarjeta_kpi(
            "Benchmarks",
            str(len(by_benchmark)),
            subtexto="Referencias metodológicas.",
            help_text=benchmarks_txt,
        )


    seccion("Activos seleccionados para el análisis")

    portfolio_config = st.session_state.get("portfolio_config", {}) or {}
    selected_tickers = [
        str(ticker).upper()
        for ticker in portfolio_config.get("tickers", []) or []
    ]

    asset_by_ticker = {
        str(asset.get("ticker", "")).upper(): asset
        for asset in assets
    }

    if selected_tickers:
        filtered_assets = [
            asset_by_ticker[ticker]
            for ticker in selected_tickers
            if ticker in asset_by_ticker
        ]
        missing_tickers = [
            ticker
            for ticker in selected_tickers
            if ticker not in asset_by_ticker
        ]

        if missing_tickers:
            st.warning(
                "Algunos tickers seleccionados no están disponibles en el universo del backend: "
                + ", ".join(missing_tickers)
            )
    else:
        if view_mode == "Un activo" and selected_label:
            filtered_assets = [asset_map[selected_label]]
        elif view_mode == "Resumen":
            filtered_assets = default_assets
        else:
            filtered_assets = assets

    if not filtered_assets:
        st.warning("No hay activos para mostrar con la configuración actual.")
        st.stop()

    compact_rows = []

    for asset in filtered_assets:
        profile = _build_asset_profile(
            name=asset.get("name", ""),
            ticker=asset.get("ticker", ""),
            country=display_country(asset),
            is_default=bool(asset.get("default")),
        )

        risk_text = profile.get("riesgo", "N/D")
        risk_lower = risk_text.lower()

        if "medio-alto" in risk_lower:
            risk_level = "Medio-alto"
        elif "alto" in risk_lower:
            risk_level = "Alto"
        elif "medio" in risk_lower:
            risk_level = "Medio"
        elif "bajo" in risk_lower:
            risk_level = "Bajo"
        else:
            risk_level = "Variable"

        compact_rows.append(
            {
                "Ticker": asset.get("ticker", "N/D"),
                "Activo": asset.get("name", "N/D"),
                "País": display_country(asset),
                "Clase": asset.get("asset_type", "N/D"),
                "Riesgo": risk_level,
                "Benchmark": asset.get("benchmark_ticker", "N/D"),
            }
        )

    st.dataframe(
        pd.DataFrame(compact_rows),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width="small"),
            "Activo": st.column_config.TextColumn("Activo", width="medium"),
            "País": st.column_config.TextColumn("País", width="small"),
            "Clase": st.column_config.TextColumn("Clase", width="medium"),
            "Riesgo": st.column_config.TextColumn("Riesgo", width="small"),
            "Benchmark": st.column_config.TextColumn("Benchmark", width="small"),
        },
    )


with tab_rf_benchmark:
    _render_rf_and_benchmark_tab()
