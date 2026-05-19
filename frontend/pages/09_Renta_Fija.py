from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.cards import render_info_card, render_meta_row
from ui.dashboard_ui import (
    header_dashboard,
    nota,
    plot_card_footer,
    plot_card_header,
    seccion,
    tarjeta_kpi,
)
from ui.page_setup import setup_dashboard_page
from ui.plot_style import style_plotly_figure


setup_dashboard_page(
    page_title="Renta Fija",
    page_icon="💵",
)

header_dashboard(
    title="Módulo 9 — Renta fija",
    subtitle="Ajuste de curva Nelson-Siegel y lectura de estructura temporal de tasas.",
)

client = get_api_client()

seccion("Parámetros de curva")

with st.sidebar:
    st.markdown("### Curva de rendimiento")
    maturities_text = st.text_input("Vencimientos en años", "1,2,5,10")
    yields_text = st.text_input("Tasas observadas", "0.03,0.035,0.04,0.045")

try:
    maturities = [float(x.strip()) for x in maturities_text.split(",") if x.strip()]
    yields = [float(x.strip()) for x in yields_text.split(",") if x.strip()]
except ValueError:
    maturities = []
    yields = []

render_info_card(
    "Nelson-Siegel",
    "Este módulo ajusta una curva de rendimiento a partir de vencimientos y tasas observadas.",
)

if len(maturities) != len(yields) or len(maturities) < 4:
    st.warning("Ingresa al menos 4 vencimientos y 4 tasas observadas con la misma longitud.")
else:
    payload = {
        "maturities": maturities,
        "yields": yields,
    }

    if st.button("Ajustar curva", type="primary"):
        try:
            result = client.post("/valuation/nelson-siegel", json_payload=payload, include_api_key=True)

            params = result["params"]

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                tarjeta_kpi("Beta 0", f"{params['beta0']:.4f}")
            with col2:
                tarjeta_kpi("Beta 1", f"{params['beta1']:.4f}")
            with col3:
                tarjeta_kpi("Beta 2", f"{params['beta2']:.4f}")
            with col4:
                tarjeta_kpi("RMSE", f"{result['rmse']:.6f}")

            render_meta_row(
                {
                    "Modelo": result.get("curve_type", "Nelson-Siegel"),
                    "Tau": f"{params['tau']:.4f}",
                    "Puntos": str(len(maturities)),
                }
            )

            df = pd.DataFrame(
                {
                    "maturity": maturities,
                    "observed_yield": yields,
                }
            ).sort_values("maturity")

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df["maturity"],
                    y=df["observed_yield"],
                    mode="markers+lines",
                    name="Curva observada",
                )
            )

            fig.update_layout(
                title="Curva observada de rendimiento",
                xaxis_title="Vencimiento en años",
                yaxis_title="Tasa",
            )

            plot_card_header("Curva de rendimiento")
            st.plotly_chart(style_plotly_figure(fig), use_container_width=True)
            plot_card_footer("La curva permite interpretar nivel, pendiente y curvatura de las tasas.")

            nota(result.get("summary", "Curva ajustada correctamente."))

        except ApiClientError as exc:
            st.error(f"Error al consumir backend de renta fija: {exc.message}")
        except Exception as exc:
            st.error(f"Error inesperado: {exc}")
