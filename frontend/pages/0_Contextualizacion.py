from __future__ import annotations

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
from services.api_client import get_api_client, ApiClientError


def _build_asset_role(name: str, ticker: str, country: str, is_default: bool) -> dict[str, str]:
    ticker_u = (ticker or "").upper()
    name_l = (name or "").lower()
    country_l = (country or "").lower()

    if "bp" in name_l or "shel" in ticker_u or "xom" in ticker_u:
        return {
            "rol": "Cobertura sectorial",
            "aporte": "Exposición energética y sensibilidad macroeconómica.",
            "tesis": "Ayuda a diversificar frente a activos de consumo y retail.",
        }

    if "femsa" in name_l or "kof" in ticker_u:
        return {
            "rol": "Exposición regional",
            "aporte": "Latinoamérica, consumo y estructura operativa diversificada.",
            "tesis": "Introduce sesgo regional y mezcla entre estabilidad y crecimiento.",
        }

    if "seven" in name_l or "atd" in ticker_u or "carrefour" in name_l or "wmt" in ticker_u:
        return {
            "rol": "Retail defensivo",
            "aporte": "Consumo recurrente, operación internacional y resiliencia relativa.",
            "tesis": "Aporta estabilidad comparativa dentro del portafolio.",
        }

    if "apple" in name_l or "microsoft" in name_l or "visa" in name_l:
        return {
            "rol": "Crecimiento global",
            "aporte": "Exposición a compañías de gran escala con sesgo de crecimiento.",
            "tesis": "Aumenta potencial de retorno esperado con mayor sensibilidad al mercado.",
        }

    if "toyota" in name_l or "nestle" in name_l or "santander" in name_l:
        return {
            "rol": "Diversificación internacional",
            "aporte": "Amplía exposición geográfica y sectorial del portafolio.",
            "tesis": "Reduce concentración por región o industria.",
        }

    if is_default:
        return {
            "rol": "Activo base del proyecto",
            "aporte": "Hace parte del núcleo inicial definido en el backend.",
            "tesis": "Sirve como universo principal para el tablero.",
        }

    return {
        "rol": "Activo complementario",
        "aporte": f"Permite ampliar el universo internacional desde {country}.",
        "tesis": "Ayuda a probar escenarios de selección y búsqueda de activos.",
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

    show_general_read = st.checkbox(
        "Mostrar lectura general del portafolio",
        value=True,
        key="ctx_show_general_read",
    )
    show_connection = st.checkbox(
        "Mostrar conexión con módulos",
        value=True,
        key="ctx_show_connection",
    )
    show_default_only = st.checkbox(
        "Mostrar solo activos base",
        value=False,
        key="ctx_show_default_only",
    )

header_dashboard(
    "Módulo 0 - Contextualización del portafolio",
    "Presenta el universo de activos, su rol dentro del proyecto y la lógica general del tablero conectado al backend",
    modo=modo,
)

if load_error:
    st.error(load_error)
    st.stop()

if modo == "General":
    nota(
        "Este módulo introduce el universo de activos definido por el backend y resume por qué cada uno puede aportar diversificación, estabilidad o sensibilidad sectorial al portafolio."
    )
else:
    nota(
        "En modo estadístico, esta vista contextualiza el universo invertible, la selección base del proyecto y la relación entre composición, benchmark y módulos analíticos posteriores."
    )

seccion("Resumen del universo")

default_assets = [a for a in assets if a.get("default") is True]
extra_assets = [a for a in assets if a.get("default") is not True]
countries = sorted({a.get("country", "N/D") for a in assets})
tickers = [a.get("ticker", "") for a in assets]

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
        ("Benchmark backend", "ACWI"),
        ("Modo", modo),
        ("Fuente", "API backend /assets"),
    ]
)

if show_general_read:
    sharpe_help = help_map.get("sharpe_ratio", {})
    efficient_frontier_help = help_map.get("efficient_frontier", {})
    correlation_help = help_map.get("correlation_heatmap", {})

    render_info_card(
        "Lectura general del portafolio",
        (
            "La capa de contexto sirve para conectar selección de activos, benchmark global, "
            "riesgo extremo, optimización y métricas de desempeño. "
            f"Sharpe: {sharpe_help.get(modo.lower(), 'Ayuda no disponible')} "
            f"Frontera eficiente: {efficient_frontier_help.get(modo.lower(), 'Ayuda no disponible')} "
            f"Correlación: {correlation_help.get(modo.lower(), 'Ayuda no disponible')}"
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

for asset in filtered_assets:
    role_info = _build_asset_role(
        name=asset.get("name", ""),
        ticker=asset.get("ticker", ""),
        country=asset.get("country", ""),
        is_default=bool(asset.get("default")),
    )

    titulo_con_ayuda(
        f"{asset.get('name', 'Activo')} ({asset.get('ticker', 'N/D')})",
        "Resumen contextual del activo dentro del universo disponible.",
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

    col_left, col_right = st.columns([1.2, 1.8], gap="large")

    with col_left:
        tarjeta_kpi(
            "Rol en portafolio",
            role_info["rol"],
            subtexto=role_info["aporte"],
            help_text="Lectura funcional del activo dentro del portafolio y del dashboard.",
        )

    with col_right:
        render_info_card(
            "Tesis visual de interpretación",
            role_info["tesis"],
        )

    st.markdown("")

seccion("Conexión con módulos del dashboard")

if show_connection:
    render_chip_row(
        [
            "01 Técnico",
            "02 Rendimientos",
            "03 GARCH",
            "04 CAPM",
            "05 VaR / CVaR",
            "06 Markowitz",
            "07 Alertas",
            "08 Macro / Benchmark",
            "09 Panel de decisión",
        ]
    )

    benchmark_help = help_map.get("benchmark_comparison", {})
    var_help = help_map.get("var", {})
    capm_help = help_map.get("beta", {})

    render_info_card(
        "Cómo se conecta esta vista con el resto del proyecto",
        (
            "Desde aquí se define qué activos forman parte del análisis. "
            f"Benchmark: {benchmark_help.get(modo.lower(), 'Ayuda no disponible')} "
            f"VaR: {var_help.get(modo.lower(), 'Ayuda no disponible')} "
            f"Beta: {capm_help.get(modo.lower(), 'Ayuda no disponible')}"
        ),
    )
else:
    nota("La conexión con módulos quedó oculta desde el panel lateral.")