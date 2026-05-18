from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from ui.page_setup import setup_dashboard_page
from ui.dashboard_ui import (
    header_dashboard,
    nota,
    seccion,
    titulo_con_ayuda,
    tarjeta_kpi,
)
from ui.cards import render_chip_row, render_info_card, render_meta_row
from ui.theme import image_to_base64, safe_text
from services.api_client import get_api_client, ApiClientError


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
            '<div style="font-size:0.80rem;font-weight:900;letter-spacing:0.08em;'
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
    country = asset.get("country", "N/D")
    base_tag = "S?" if asset.get("default") else "No"
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
            '<div style="font-size:0.80rem;font-weight:900;letter-spacing:0.08em;'
            'text-transform:uppercase;color:var(--text-muted);margin-bottom:0.7rem;">'
            'Lectura financiera del activo'
            '</div>'
            f'<div style="font-size:0.96rem;line-height:1.65;color:var(--text-soft);'
            f'font-weight:600;margin-bottom:0.85rem;">{safe_text(profile["tesis"])}</div>'
            '<div style="display:flex;flex-wrap:wrap;gap:0.45rem;margin-bottom:0.8rem;">'
            f'<span class="ui-chip"><strong>Pa?s:</strong>&nbsp;{safe_text(country)}</span>'
            f'<span class="ui-chip"><strong>Activo base:</strong>&nbsp;{base_tag}</span>'
            f'<span class="ui-chip"><strong>Clase:</strong>&nbsp;{safe_text(asset_type)}</span>'
            f'<span class="ui-chip"><strong>Benchmark:</strong>&nbsp;{safe_text(benchmark_ticker)}</span>'
            f'<span class="ui-chip"><strong>Fuente:</strong>&nbsp;{safe_text(source)}</span>'
            '</div>'
            f'<div style="font-size:0.92rem;line-height:1.58;color:var(--text-soft);font-weight:600;">'
            f'<strong>Riesgo:</strong> {safe_text(profile["riesgo"])}<br>'
            f'<strong>Benchmark metodol?gico:</strong> {safe_text(benchmark_description)}<br>'
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
        country=asset.get("country", ""),
        is_default=bool(asset.get("default")),
    )

    titulo_con_ayuda(
        f"{asset.get('name', 'Activo')} ({asset.get('ticker', 'N/D')})",
        "Resumen contextual y lectura financiera del activo dentro del universo del proyecto.",
        nivel=3,
    )

    render_chip_row(
        [
            f"País: {asset.get('country', 'N/D')}",
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
            "Los precios descargados desde yfinance pueden venir en la moneda de cotización de cada mercado. "
            "Por ejemplo, BP cotiza en Londres, Carrefour en euros, Couche-Tard en dólares canadienses, "
            "FEMSA en pesos mexicanos y Seven & i en yenes japoneses. "
            "Para evitar mezclar monedas dentro de una misma matriz de rendimientos, el backend convierte "
            "históricamente los precios a USD usando la divisa correspondiente antes de calcular rendimientos, "
            "CAPM, VaR/CVaR, GARCH y Markowitz."
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

    st.dataframe(pd.DataFrame(conversion_rows), width="stretch", hide_index=True)

    seccion("Tasa libre de riesgo")

    render_info_card(
        "Criterio usado para la Rf",
        (
            "Después de convertir los activos a USD, el proyecto usa una tasa libre de riesgo común en USD. "
            "Esto permite calcular Sharpe, CAPM y Markowitz con un criterio homogéneo. "
            "No se usa una Rf diferente por activo dentro de Markowitz, porque eso mezclaría tasas de monedas "
            "distintas y haría menos comparable la frontera eficiente."
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

    st.dataframe(pd.DataFrame(rf_rows), width="stretch", hide_index=True)

    render_meta_row(
        [
            ("Rf principal", "^IRX"),
            ("Moneda base", "USD"),
            ("Uso", "Sharpe, CAPM y Markowitz"),
        ]
    )

    seccion("Benchmark del portafolio")

    render_info_card(
        "Benchmark usado: ACWI",
        (
            "El benchmark del proyecto es ACWI, una referencia global de renta variable. "
            "Se utiliza porque el portafolio combina activos de diferentes países y no sería adecuado "
            "compararlo únicamente contra un índice local. ACWI permite evaluar si el portafolio internacional "
            "genera un desempeño razonable frente a una referencia global diversificada."
        ),
    )

    benchmark_rows = [
        {
            "Benchmark": "ACWI",
            "Tipo": "Referencia global de renta variable",
            "Uso en el proyecto": "Comparación de desempeño, CAPM, beta, alpha de Jensen y métricas relativas.",
            "Justificación": "Es coherente con un portafolio internacional y multimoneda convertido a USD.",
        }
    ]

    st.dataframe(pd.DataFrame(benchmark_rows), width="stretch", hide_index=True)

    render_info_card(
        "Relación entre Rf, moneda y benchmark",
        (
            "La conversión histórica a USD permite que los retornos de los activos sean comparables entre sí. "
            "Una vez todo está expresado en una moneda común, se usa una Rf en USD y un benchmark global en USD. "
            "Así, las métricas de Sharpe, beta, alpha y frontera eficiente quedan alineadas bajo el mismo marco metodológico."
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

with filtros_sidebar:
    view_mode = st.radio(
        "Vista",
        ["Resumen", "Un activo", "Todos"],
        index=0,
        key="ctx_view_mode",
    )

    asset_labels = []
    asset_map: dict[str, dict] = {}
    for asset in assets:
        label = f"{asset['name']} · {asset['ticker']} · {asset['country']}"
        asset_labels.append(label)
        asset_map[label] = asset

    selected_label = None
    if view_mode == "Un activo" and asset_labels:
        selected_label = st.selectbox(
            "Selecciona un activo",
            options=asset_labels,
            key="ctx_asset_select",
        )

    show_general_read = True
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
    countries = sorted({a.get("country", "N/D") for a in assets})

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

    render_meta_row(
        [
            ("Benchmark global de referencia", "ACWI"),
            ("Moneda metodológica", "USD"),
            ("Modo", modo),
            ("Fuente", "API backend /assets"),
        ]
    )

    render_meta_row(
        [
            ("Activos habilitados para Perri", str(len(perri_assets))),
            (
                "Clases de activo",
                " · ".join([f"{k}: {v}" for k, v in sorted(by_asset_type.items())]),
            ),
            (
                "Benchmarks metodológicos",
                " · ".join([f"{k}: {v}" for k, v in sorted(by_benchmark.items())]),
            ),
        ]
    )

    if show_general_read:
        render_info_card(
            "Lectura financiera del portafolio",
            (
                "Este universo combina consumo defensivo, retail internacional, exposición regional y un componente energético más cíclico. "
                "Por eso no todos los activos reaccionan igual ante el mercado: algunos aportan estabilidad relativa, mientras otros introducen "
                "más sensibilidad macroeconómica, sectorial o cambiaria. Esa mezcla hace que la contextualización sea importante antes de pasar "
                "a módulos de riesgo, CAPM, VaR y optimización."
            ),
        )

    seccion("Descripción estratégica del portafolio")

    render_info_card(
        "Lógica financiera del conjunto",
        (
            "Este portafolio académico no está construido sobre una sola industria ni sobre una sola región, sino sobre una combinación "
            "de emisores internacionales con perfiles de riesgo heterogéneos. Eso implica que su lectura no debe reducirse a un único "
            "benchmark sectorial, porque cada activo responde a motores distintos: consumo defensivo, dinámica minorista internacional, "
            "exposición emergente, riesgo energético y sensibilidad macro. "
            "Desde una perspectiva financiera, esta diversidad permite estudiar diversificación real, diferencia de betas, sensibilidad "
            "regional y contraste entre activos más estables y más cíclicos."
        ),
    )

    seccion("Activos del universo")

    filtered_assets = default_assets if show_default_only else assets

    if view_mode == "Un activo" and selected_label:
        filtered_assets = [asset_map[selected_label]]
    elif view_mode == "Resumen":
        filtered_assets = default_assets

    if not filtered_assets:
        st.warning("No hay activos para mostrar con el filtro actual.")
        st.stop()

    if view_mode == "Un activo":
        for asset in filtered_assets:
            _render_asset_block(asset, modo)
    else:
        for pair in _chunks(filtered_assets, 2):
            col_a, col_b = st.columns(2, gap="large")

            with col_a:
                _render_asset_block(pair[0], modo)

            if len(pair) > 1:
                with col_b:
                    _render_asset_block(pair[1], modo)

with tab_rf_benchmark:
    _render_rf_and_benchmark_tab()