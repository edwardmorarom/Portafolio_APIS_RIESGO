from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.cards import render_info_card, render_meta_row
from ui.dashboard_ui import header_dashboard, nota, plot_card_footer, plot_card_header, seccion, tarjeta_kpi
from ui.page_setup import setup_dashboard_page
from ui.plot_style import style_plotly_figure


def _parse_float_list(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def _format_pct(value: float) -> str:
    return f"{float(value):.2%}"


def _format_num(value: float) -> str:
    return f"{float(value):,.4f}"


def _nelson_siegel_curve(maturities: np.ndarray, tau: float, beta0: float, beta1: float, beta2: float) -> np.ndarray:
    arg = np.maximum(maturities / tau, 1e-9)
    factor1 = (1 - np.exp(-arg)) / arg
    factor2 = factor1 - np.exp(-arg)
    return beta0 + beta1 * factor1 + beta2 * factor2


modo, filtros_panel = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    filtros_label="Parámetros de renta fija",
    filtros_expanded=True,
    page_title="Renta Fija",
    page_icon="💵",
)

client = get_api_client()

with filtros_panel:
    st.markdown("#### Curva Nelson-Siegel")
    maturities_text = st.text_input("Vencimientos en años", "1,2,5,10,20,30")
    yields_text = st.text_input("Tasas observadas", "0.030,0.034,0.039,0.043,0.047,0.049")

    st.markdown("#### Bono de referencia")
    face_value = st.number_input("Valor nominal", min_value=1.0, value=1000.0, step=100.0)
    coupon_rate = st.number_input("Cupón anual", min_value=0.0, value=0.045, step=0.005, format="%.4f")
    maturity_years = st.number_input("Vencimiento del bono", min_value=1, value=7, step=1)
    market_yield = st.number_input("Yield de mercado", min_value=0.0, value=0.048, step=0.005, format="%.4f")
    run_analysis = st.button("Calcular renta fija", type="primary", use_container_width=True)

header_dashboard(
    "Renta fija",
    "Curva Nelson-Siegel, métricas de bono y lectura de sensibilidad a tasas.",
    modo=modo,
)

tab_curve, tab_bond, tab_read = st.tabs(["Curva", "Bono", "Lectura"])

try:
    maturities = _parse_float_list(maturities_text)
    yields = _parse_float_list(yields_text)
except ValueError:
    maturities = []
    yields = []

if not run_analysis:
    nota("Ajusta los parámetros y ejecuta el cálculo para construir la curva y valorar el bono.")

curve_result: dict | None = None
bond_result: dict | None = None
if run_analysis:
    if len(maturities) != len(yields) or len(maturities) < 4:
        st.error("Ingresa al menos 4 vencimientos y 4 tasas observadas con la misma longitud.")
    else:
        try:
            curve_result = client.post(
                "/valuation/nelson-siegel",
                json_payload={"maturities": maturities, "yields": yields},
                include_api_key=True,
            )
            bond_result = client.post(
                "/valuation/bond-metrics",
                json_payload={
                    "face_value": float(face_value),
                    "coupon_rate": float(coupon_rate),
                    "maturity_years": int(maturity_years),
                    "market_yield": float(market_yield),
                },
                include_api_key=True,
            )
        except ApiClientError as exc:
            st.error(f"Error al consumir backend de renta fija: {exc.message}")
        except Exception as exc:
            st.error(f"Error inesperado: {exc}")

with tab_curve:
    seccion("Estructura temporal")

    if curve_result:
        params = curve_result["params"]
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            tarjeta_kpi("Nivel", _format_pct(params["beta0"]), subtexto="Beta 0")
        with c2:
            tarjeta_kpi("Pendiente", _format_pct(params["beta1"]), subtexto="Beta 1")
        with c3:
            tarjeta_kpi("Curvatura", _format_pct(params["beta2"]), subtexto="Beta 2")
        with c4:
            tarjeta_kpi("RMSE", _format_num(curve_result["rmse"]), subtexto="Error de ajuste")

        grid = np.linspace(min(maturities), max(maturities), 120)
        fitted = _nelson_siegel_curve(
            grid,
            tau=params["tau"],
            beta0=params["beta0"],
            beta1=params["beta1"],
            beta2=params["beta2"],
        )

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=maturities, y=yields, mode="markers", name="Observado"))
        fig.add_trace(go.Scatter(x=grid, y=fitted, mode="lines", name="Nelson-Siegel"))

        plot_card_header(
            "Curva ajustada",
            "Compara tasas observadas contra la curva suavizada Nelson-Siegel.",
            modo=modo,
        )
        st.plotly_chart(
            style_plotly_figure(
                fig,
                modo=modo,
                title="Curva de rendimiento",
                xaxis_title="Vencimiento en años",
                yaxis_title="Tasa",
            ),
            use_container_width=True,
        )
        plot_card_footer("Una curva más inclinada suele anticipar mayor prima por plazo; una curva plana reduce esa compensación.")
    else:
        render_info_card("Curva pendiente", "Ejecuta el cálculo para ver parámetros, ajuste y visualización.")

with tab_bond:
    seccion("Métricas del bono")

    if bond_result:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            tarjeta_kpi("Precio", f"${bond_result['price']:,.2f}", subtexto="Valor teórico")
        with c2:
            tarjeta_kpi("Duración", _format_num(bond_result["duration"]), subtexto="Macaulay")
        with c3:
            tarjeta_kpi("Duración mod.", _format_num(bond_result["modified_duration"]), subtexto="Sensibilidad")
        with c4:
            tarjeta_kpi("Convexidad", _format_num(bond_result["convexity"]), subtexto="Curvatura precio-tasa")

        render_meta_row(
            {
                "Nominal": f"${face_value:,.2f}",
                "Cupón": _format_pct(coupon_rate),
                "Yield": _format_pct(market_yield),
                "Vencimiento": f"{int(maturity_years)} años",
            }
        )
    else:
        render_info_card("Bono pendiente", "Ejecuta el cálculo para obtener precio, duración y convexidad.")

with tab_read:
    seccion("Lectura ejecutiva")
    render_info_card(
        "Uso financiero",
        (
            "Nelson-Siegel resume nivel, pendiente y curvatura de la estructura temporal. "
            "La duración modificada estima la pérdida porcentual aproximada ante un aumento de 100 pb en la tasa, "
            "mientras que la convexidad corrige esa aproximación cuando los movimientos son grandes."
        ),
    )

    if curve_result and bond_result:
        params = curve_result["params"]
        duration_loss = bond_result["modified_duration"] * 0.01
        nota(
            f"Con una duración modificada de {bond_result['modified_duration']:.2f}, un alza de 100 pb implicaría "
            f"una pérdida aproximada de {_format_pct(duration_loss)} antes de ajustar por convexidad. "
            f"El nivel estimado de la curva es {_format_pct(params['beta0'])}."
        )
