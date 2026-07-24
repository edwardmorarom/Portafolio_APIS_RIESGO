from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.cards import render_info_card, render_meta_row
from ui.dashboard_filters import render_filter_help
from ui.dashboard_ui import header_dashboard, nota, plot_card_footer, plot_card_header, seccion, tarjeta_kpi
from ui.formatting import format_money, format_number, format_percent
from ui.page_setup import setup_dashboard_page
from ui.plot_style import style_plotly_figure
from ui.portfolio_state import render_portfolio_scope_note


CURVE_MATURITY_COL = "Vencimiento (a\u00f1os)"
CURVE_YIELD_COL = "Tasa observada"


def _normalize_curve_columns(df: pd.DataFrame) -> pd.DataFrame:
    aliases = {
        "Vencimiento (años)": CURVE_MATURITY_COL,
        "Vencimiento (anos)": CURVE_MATURITY_COL,
        "Vencimiento": CURVE_MATURITY_COL,
        "maturity": CURVE_MATURITY_COL,
        "maturity_years": CURVE_MATURITY_COL,
        "Tasa": CURVE_YIELD_COL,
        "yield": CURVE_YIELD_COL,
        "yield_rate": CURVE_YIELD_COL,
    }
    return pd.DataFrame(df).rename(columns={col: aliases.get(str(col), col) for col in pd.DataFrame(df).columns})


def _nelson_siegel_curve(maturities: np.ndarray, tau: float, beta0: float, beta1: float, beta2: float) -> np.ndarray:
    arg = np.maximum(maturities / tau, 1e-9)
    factor1 = (1 - np.exp(-arg)) / arg
    factor2 = factor1 - np.exp(-arg)
    return beta0 + beta1 * factor1 + beta2 * factor2


def _add_months(value: date, months: int) -> date:
    return (pd.Timestamp(value) + pd.DateOffset(months=months)).date()


def _periodic_rate(annual_rate: float, rate_type: str, frequency: int) -> float:
    if rate_type == "efectiva_anual":
        return (1.0 + annual_rate) ** (1.0 / frequency) - 1.0
    return annual_rate / frequency


def _coupon_dates(issue_date: date, maturity_date: date, frequency: int) -> list[date]:
    months = max(1, 12 // max(1, frequency))
    dates = [maturity_date]
    cursor = maturity_date
    while True:
        previous = _add_months(cursor, -months)
        if previous <= issue_date:
            break
        dates.append(previous)
        cursor = previous
    return sorted(dates)


def _coupon_window(issue_date: date, maturity_date: date, settlement_date: date, frequency: int) -> tuple[date, date]:
    previous = issue_date
    for payment_date in _coupon_dates(issue_date, maturity_date, frequency):
        if settlement_date < payment_date:
            return previous, payment_date
        previous = payment_date
    raise ValueError("No hay cupon pendiente para la fecha de negociacion enviada.")


def _price_from_cashflows(cashflows: list[dict], periodic_yield: float, frequency: int) -> float:
    return float(
        sum(
            float(item["cashflow"])
            / ((1.0 + periodic_yield) ** (float(item["days_from_settlement"]) * frequency / 365.0))
            for item in cashflows
        )
    )


def _simulate_bond_purchase_locally(payload: dict) -> dict:
    issue_date = date.fromisoformat(payload["issue_date"])
    maturity_date = date.fromisoformat(payload["maturity_date"])
    settlement_date = date.fromisoformat(payload["settlement_date"])
    face_value = float(payload["face_value"])
    coupon_rate = float(payload["coupon_rate"])
    frequency = int(payload["coupon_frequency"])
    market_yield = float(payload["market_yield"])
    clean_price_pct = float(payload["clean_price_pct"])
    fees_pct = float(payload["fees_pct"])
    fixed_fee = float(payload["fixed_fee"])

    coupon_periodic_rate = _periodic_rate(coupon_rate, payload["coupon_rate_type"], frequency)
    market_yield_periodic = _periodic_rate(market_yield, payload["market_yield_type"], frequency)
    previous_coupon, next_coupon = _coupon_window(issue_date, maturity_date, settlement_date, frequency)
    coupon_period_days = max((next_coupon - previous_coupon).days, 1)
    accrued_days = max((settlement_date - previous_coupon).days, 0)
    coupon_per_period = face_value * coupon_periodic_rate
    accrued_interest = coupon_per_period * min(accrued_days / coupon_period_days, 1.0)
    clean_price_value = face_value * clean_price_pct / 100.0
    dirty_price = clean_price_value + accrued_interest
    fees = dirty_price * fees_pct / 100.0 + fixed_fee
    total_purchase = dirty_price + fees

    cashflows: list[dict] = []
    period = 1
    all_coupon_dates = _coupon_dates(issue_date, maturity_date, frequency)
    for payment_date in all_coupon_dates:
        if payment_date <= settlement_date:
            continue
        days_from_settlement = int((payment_date - settlement_date).days)
        period_exponent = days_from_settlement * frequency / 365.0
        cashflow = coupon_per_period + (face_value if payment_date == maturity_date else 0.0)
        discount_factor = 1.0 / ((1.0 + market_yield_periodic) ** period_exponent)
        cashflows.append(
            {
                "payment_date": payment_date,
                "days_from_settlement": days_from_settlement,
                "period": int(period),
                "cashflow": float(cashflow),
                "discount_factor": float(discount_factor),
                "present_value": float(cashflow * discount_factor),
            }
        )
        period += 1

    if not cashflows:
        raise ValueError("No hay flujos pendientes para la fecha de negociacion enviada.")

    theoretical_price = float(sum(item["present_value"] for item in cashflows))
    future_value = float(sum(item["cashflow"] for item in cashflows))
    expected_gain_simple = future_value - total_purchase
    total_bond_days = (maturity_date - issue_date).days
    seller_holding_days = (settlement_date - issue_date).days
    seller_proportion = seller_holding_days / total_bond_days if total_bond_days > 0 else 0.0
    total_bond_gain = coupon_per_period * len(all_coupon_dates)
    seller_commission = total_bond_gain * seller_proportion
    buyer_net_gain = expected_gain_simple - seller_commission
    buyer_npv = theoretical_price - total_purchase
    macaulay_duration = float(
        sum((item["days_from_settlement"] / 365.0) * item["present_value"] for item in cashflows) / theoretical_price
    )
    modified_duration = macaulay_duration / (1.0 + market_yield_periodic)
    yield_down = _periodic_rate(max(market_yield - 0.0001, 0.0), payload["market_yield_type"], frequency)
    yield_up = _periodic_rate(market_yield + 0.0001, payload["market_yield_type"], frequency)
    dv01 = max(0.0, (_price_from_cashflows(cashflows, yield_down, frequency) - _price_from_cashflows(cashflows, yield_up, frequency)) / 2.0)
    dv01_approx = modified_duration * theoretical_price * 0.0001
    interpretation = (
        "La compra luce favorable frente al yield ingresado: el precio teorico supera el total pagado."
        if theoretical_price > total_purchase
        else "La compra exige cautela: el comprador estaria pagando caro frente al yield ingresado."
    )

    return {
        "position": "purchase",
        "inputs": payload,
        "rates": {
            "coupon_periodic_rate": float(coupon_periodic_rate),
            "market_yield_periodic": float(market_yield_periodic),
        },
        "coupon_dates": {
            "previous_coupon_date": previous_coupon,
            "next_coupon_date": next_coupon,
            "accrued_days": int(accrued_days),
            "coupon_period_days": int(coupon_period_days),
        },
        "metrics": {
            "coupon_per_period": float(coupon_per_period),
            "accrued_interest": float(accrued_interest),
            "clean_price_value": float(clean_price_value),
            "dirty_price": float(dirty_price),
            "fees": float(fees),
            "total_purchase": float(total_purchase),
            "theoretical_price": float(theoretical_price),
            "future_value": float(future_value),
            "expected_gain_simple": float(expected_gain_simple),
            "total_bond_gain": float(total_bond_gain),
            "seller_commission": float(seller_commission),
            "buyer_net_gain": float(buyer_net_gain),
            "buyer_npv": float(buyer_npv),
            "macaulay_duration": float(macaulay_duration),
            "modified_duration": float(modified_duration),
            "dv01": float(dv01),
            "dv01_approx": float(dv01_approx),
            "remaining_periods": int(len(cashflows)),
        },
        "cashflows": cashflows,
        "interpretation": interpretation,
    }


def _render_module_switch() -> str:
    current = st.session_state.get("fixed_income_module_view", "Renta fija")
    if current not in {"Renta fija", "Compra de bono TES"}:
        current = "Renta fija"
        st.session_state.fixed_income_module_view = current
    left, right = st.columns(2)
    with left:
        if st.button(
            "Renta fija",
            key="fixed_income_view_curve",
            type="primary" if current == "Renta fija" else "secondary",
            use_container_width=True,
        ):
            st.session_state.fixed_income_module_view = "Renta fija"
            st.rerun()
    with right:
        if st.button(
            "Compra de bono TES",
            key="fixed_income_view_purchase",
            type="primary" if current == "Compra de bono TES" else "secondary",
            use_container_width=True,
        ):
            st.session_state.fixed_income_module_view = "Compra de bono TES"
            st.rerun()
    return st.session_state.get("fixed_income_module_view", "Renta fija")


def _bond_sensitivity_df(bond_result: dict) -> pd.DataFrame:
    rows = bond_result.get("sensitivity", []) or []
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    numeric_cols = [
        "shock_bp",
        "shocked_yield",
        "price_linear_duration",
        "price_duration_convexity",
        "price_exact_reprice",
        "pct_change_linear_duration",
        "pct_change_duration_convexity",
        "pct_change_exact_reprice",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["shock_bp"]).sort_values("shock_bp")


def _build_bond_sensitivity_figure(df: pd.DataFrame, modo: str) -> go.Figure:
    fig = go.Figure()
    series = [
        ("pct_change_linear_duration", "Lineal con duracion"),
        ("pct_change_duration_convexity", "Duracion + convexidad"),
        ("pct_change_exact_reprice", "Reprice exacto"),
    ]

    for column, label in series:
        if column not in df.columns:
            continue
        fig.add_trace(
            go.Scatter(
                x=df["shock_bp"],
                y=df[column],
                mode="lines+markers",
                name=label,
                line=dict(width=2.4),
            )
        )

    return style_plotly_figure(
        fig,
        modo=modo,
        title="Sensibilidad precio-tasa",
        xaxis_title="Shock de tasa (pb)",
        yaxis_title="Cambio porcentual del precio",
        show_xgrid=True,
        show_ygrid=True,
    )


def _classify_curve_shape(maturities: list[float], yields: list[float]) -> tuple[str, float, str]:
    curve = sorted(zip(maturities, yields), key=lambda item: item[0])
    if len(curve) < 2:
        return "N/D", 0.0, "No hay puntos suficientes para clasificar la curva."

    short_rate = float(curve[0][1])
    long_rate = float(curve[-1][1])
    slope_bp = (long_rate - short_rate) * 10000.0

    if slope_bp > 25:
        return (
            "Normal",
            slope_bp,
            "La curva normal suele asociarse con expectativa de crecimiento y prima positiva por plazo.",
        )
    if slope_bp < -25:
        return (
            "Invertida",
            slope_bp,
            "La curva invertida suele leerse como tension macro: el mercado exige mas retorno en el corto plazo que en el largo.",
        )
    return (
        "Plana",
        slope_bp,
        "La curva plana sugiere transicion o incertidumbre: la prima por plazo es baja y las expectativas estan comprimidas.",
    )


def _render_bond_purchase_tab(key_prefix: str) -> None:
    c1, c2, c3 = st.columns(3)
    with c1:
        issue_date = st.date_input("Fecha de emision", value=date(2019, 10, 8), key=f"{key_prefix}_issue")
        maturity_date = st.date_input("Fecha de vencimiento", value=date(2034, 10, 18), key=f"{key_prefix}_maturity")
        max_settlement_default = (pd.Timestamp(maturity_date) - pd.DateOffset(days=1)).date()
        settlement_default = min(max(date(2026, 5, 21), issue_date), max_settlement_default)
        settlement_date = st.date_input("Fecha de negociacion", value=settlement_default, key=f"{key_prefix}_settlement")
    with c2:
        face_value_trade = st.number_input("Valor nominal", min_value=1.0, value=1_000_000_000.0, step=1_000_000.0, format="%.0f", key=f"{key_prefix}_face")
        coupon_rate_trade = st.number_input("Tasa cupon anual", min_value=0.0, value=0.0725, step=0.0025, format="%.4f", key=f"{key_prefix}_coupon")
        coupon_rate_type = st.selectbox("Tipo de tasa cupon", ["nominal_anual", "efectiva_anual"], key=f"{key_prefix}_coupon_type")
        frequency = st.selectbox("Frecuencia de cupon", [1, 2, 4], index=0, format_func=lambda value: {1: "Anual", 2: "Semestral", 4: "Trimestral"}[value], key=f"{key_prefix}_freq")
    with c3:
        market_yield_trade = st.number_input("Yield de mercado anual", min_value=0.0, value=0.09, step=0.0025, format="%.4f", key=f"{key_prefix}_yield")
        market_yield_type = st.selectbox("Tipo de yield", ["nominal_anual", "efectiva_anual"], key=f"{key_prefix}_yield_type")
        clean_price_pct = st.number_input("Precio limpio (% nominal)", min_value=0.0001, value=98.5, step=0.25, format="%.4f", key=f"{key_prefix}_clean")
        fees_pct = st.number_input("Honorarios (%)", min_value=0.0, value=0.25, step=0.05, format="%.4f", key=f"{key_prefix}_fees_pct")
        fixed_fee = st.number_input("Honorario fijo", min_value=0.0, value=0.0, step=10_000.0, format="%.0f", key=f"{key_prefix}_fixed_fee")

    if maturity_date <= issue_date:
        st.warning("La fecha de vencimiento debe ser mayor que la fecha de emision.")
        return
    if settlement_date < issue_date or settlement_date >= maturity_date:
        st.warning("La fecha de negociacion debe estar entre la emision y antes del vencimiento.")
        return

    request_payload = {
        "issue_date": issue_date.isoformat(),
        "maturity_date": maturity_date.isoformat(),
        "settlement_date": settlement_date.isoformat(),
        "face_value": float(face_value_trade),
        "coupon_rate": float(coupon_rate_trade),
        "coupon_rate_type": coupon_rate_type,
        "coupon_frequency": int(frequency),
        "market_yield": float(market_yield_trade),
        "market_yield_type": market_yield_type,
        "clean_price_pct": float(clean_price_pct),
        "fees_pct": float(fees_pct),
        "fixed_fee": float(fixed_fee),
        "currency": "COP",
    }

    try:
        result = client.post(
            "/fixed-income/bond/purchase",
            json_payload=request_payload,
            include_api_key=True,
        )
    except ApiClientError as exc:
        if exc.status_code == 404 or "not found" in exc.message.lower():
            try:
                result = _simulate_bond_purchase_locally(request_payload)
                st.info("El backend activo no tiene este endpoint cargado; se uso el simulador local de compra TES.")
            except Exception as fallback_exc:
                st.error(f"No fue posible simular la compra del bono: {fallback_exc}")
                return
        else:
            st.error(f"No fue posible simular la compra del bono: {exc.message}")
            return
    except Exception as exc:
        st.error(f"Error inesperado simulando la compra del bono: {exc}")
        return

    metrics = result["metrics"]
    coupon_dates = result["coupon_dates"]
    rates = result["rates"]

    seccion("Costo de compra")
    c1, c2, c3 = st.columns(3)
    with c1:
        tarjeta_kpi("Interes acumulado", format_money(metrics["accrued_interest"]), subtexto=f"{coupon_dates['accrued_days']} dias", help_text="Interes causado desde el ultimo cupon hasta la fecha de negociacion.")
    with c2:
        tarjeta_kpi("Precio sucio", format_money(metrics["dirty_price"]), subtexto="Precio + interes", help_text="Precio limpio monetario mas interes acumulado.")
    with c3:
        tarjeta_kpi("Total compra", format_money(metrics["total_purchase"]), subtexto="Incluye honorarios", help_text="Precio sucio mas honorarios porcentuales y fijos.")

    seccion("Valoracion del bono")
    c4, c5, c6 = st.columns(3)
    with c4:
        tarjeta_kpi("Precio teorico", format_money(metrics["theoretical_price"]), subtexto="Por yield", help_text="Valor presente de los flujos futuros descontados al yield ingresado.")
    with c5:
        tarjeta_kpi("Valor futuro", format_money(metrics["future_value"]), subtexto="Cupones + nominal", help_text="Suma simple de flujos restantes sin descuento.")
    with c6:
        tarjeta_kpi("Ganancia esperada", format_money(metrics["expected_gain_simple"]), subtexto="Futuro - total", help_text="Diferencia simple entre flujos futuros y total de compra.")

    seccion("Sensibilidad a tasa")
    c7, c8, c9 = st.columns(3)
    with c7:
        tarjeta_kpi("Duracion Macaulay", format_number(metrics["macaulay_duration"]), subtexto="Anios ponderados", help_text="Promedio ponderado del tiempo real hasta recibir los flujos futuros.")
    with c8:
        tarjeta_kpi("Duracion mod.", format_number(metrics["modified_duration"]), subtexto="Sensibilidad", help_text="Duracion Macaulay ajustada por yield periodico.")
    with c9:
        tarjeta_kpi("DV01", format_money(metrics["dv01"]), subtexto="1 punto basico", help_text="Cambio aproximado del precio ante 1 punto basico en yield.")

    holding_help = "Reparto alternativo de la ganancia total del bono según el tiempo que cada parte lo tuvo — distinto del interés acumulado de mercado mostrado arriba."
    seccion("Reparto por tenencia")
    c10, c11, c12 = st.columns(3)
    with c10:
        tarjeta_kpi("Ganancia total", format_money(metrics["total_bond_gain"]), subtexto="Cupones de toda la vida", help_text=holding_help)
    with c11:
        tarjeta_kpi("Comision vendedor", format_money(metrics["seller_commission"]), subtexto="Reparto por tiempo", help_text=holding_help)
    with c12:
        tarjeta_kpi("Ganancia neta comprador", format_money(metrics["buyer_net_gain"]), subtexto="Ajustada por tenencia", help_text=holding_help)

    st.dataframe(
        pd.DataFrame(
            [
                {"Metrica": "Precio limpio pactado", "Valor": format_money(metrics["clean_price_value"])},
                {"Metrica": "Interes acumulado", "Valor": format_money(metrics["accrued_interest"])},
                {"Metrica": "Precio sucio", "Valor": format_money(metrics["dirty_price"])},
                {"Metrica": "Honorarios", "Valor": format_money(metrics["fees"])},
                {"Metrica": "Total compra", "Valor": format_money(metrics["total_purchase"])},
                {"Metrica": "Precio teorico por yield", "Valor": format_money(metrics["theoretical_price"])},
                {"Metrica": "VPN comprador", "Valor": format_money(metrics["buyer_npv"])},
                {"Metrica": "Ganancia esperada simple", "Valor": format_money(metrics["expected_gain_simple"])},
                {"Metrica": "Ganancia total del bono", "Valor": format_money(metrics["total_bond_gain"])},
                {"Metrica": "Comision al vendedor por tenencia", "Valor": format_money(metrics["seller_commission"])},
                {"Metrica": "Ganancia neta comprador ajustada", "Valor": format_money(metrics["buyer_net_gain"])},
                {"Metrica": "Tasa cupon periodica", "Valor": format_percent(rates["coupon_periodic_rate"])},
                {"Metrica": "Yield periodico", "Valor": format_percent(rates["market_yield_periodic"])},
                {"Metrica": "Periodos restantes", "Valor": metrics["remaining_periods"]},
                {"Metrica": "Duracion Macaulay", "Valor": format_number(metrics["macaulay_duration"])},
                {"Metrica": "Duracion modificada", "Valor": format_number(metrics["modified_duration"])},
                {"Metrica": "DV01", "Valor": format_money(metrics["dv01"])},
                {"Metrica": "DV01 aproximado", "Valor": format_money(metrics["dv01_approx"])},
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    cashflows = result.get("cashflows", [])
    schedule_df = pd.DataFrame(cashflows)
    if not schedule_df.empty:
        schedule_df = schedule_df.rename(
            columns={
                "payment_date": "Fecha pago",
                "days_from_settlement": "Dias desde negociacion",
                "period": "Periodo",
                "cashflow": "Flujo",
                "discount_factor": "Factor descuento",
                "present_value": "Valor presente",
            }
        )
        schedule_df["Flujo"] = schedule_df["Flujo"].map(format_money)
        schedule_df["Factor descuento"] = schedule_df["Factor descuento"].map(lambda value: format_number(value, decimals=4))
        schedule_df["Valor presente"] = schedule_df["Valor presente"].map(format_money)
        st.dataframe(schedule_df, use_container_width=True, hide_index=True)

    nota(result.get("interpretation", "Operacion calculada correctamente."))


modo, filtros_panel = setup_dashboard_page(
    title="P.R.ED",
    subtitle="Desarrolla Tus Portafolios",
    filtros_label=None,
    filtros_expanded=False,
    page_title="Renta Fija",
    page_icon="💵",
)

client = get_api_client()

header_dashboard(
    "Renta fija",
    "Curva Nelson-Siegel, métricas de bono y lectura de sensibilidad a tasas.",
    modo=modo,
)

module_view = _render_module_switch()

if module_view == "Compra de bono TES":
    render_info_card(
        "Compra de bono TES",
        "Simula cuanto paga el comprador, que flujos futuros recibe y que riesgo de tasa asume.",
    )
    _render_bond_purchase_tab("bond_buy")
    st.stop()

render_info_card(
    "Módulo 9 - Renta fija",
    "Construye una curva Nelson-Siegel, valora bonos y estima sensibilidad a tasas para instrumentos de deuda.",
)
render_portfolio_scope_note()
render_filter_help(
    "Cómo llenar renta fija",
    "Edita la tabla de puntos de curva: vencimiento en años y tasa decimal. Ejemplo: 0.043 equivale a 4.30%. Luego define el bono a valorar.",
)

default_curve = pd.DataFrame(
    {
        CURVE_MATURITY_COL: [1, 2, 5, 10, 20, 30],
        CURVE_YIELD_COL: [0.030, 0.034, 0.039, 0.043, 0.047, 0.049],
    }
)
curve_source_note = "Curva metodologica local."
try:
    treasury_payload = client.get_treasury_curve()
    treasury_points = treasury_payload.get("points", []) if isinstance(treasury_payload, dict) else []
    if treasury_points:
        default_curve = pd.DataFrame(
            {
                CURVE_MATURITY_COL: [float(point["maturity_years"]) for point in treasury_points],
                CURVE_YIELD_COL: [float(point["yield_rate"]) for point in treasury_points],
            }
        )
        curve_source_note = treasury_payload.get("message", "Curva Treasury cargada desde backend.")
except Exception:
    pass

st.caption(curve_source_note)
curve_inputs = st.data_editor(
    default_curve,
    hide_index=True,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        CURVE_MATURITY_COL: st.column_config.NumberColumn(CURVE_MATURITY_COL, min_value=0.25, step=0.25, format="%.2f"),
        CURVE_YIELD_COL: st.column_config.NumberColumn(CURVE_YIELD_COL, min_value=0.0, max_value=1.0, step=0.001, format="%.4f"),
    },
    key="fixed_income_curve_editor",
)

b1, b2 = st.columns(2)
with b1:
    face_value = st.number_input("Valor nominal", min_value=1.0, value=1000.0, step=100.0, help="Monto principal que paga el bono al vencimiento.")
    coupon_rate = st.number_input("Cupón anual", min_value=0.0, value=0.045, step=0.005, format="%.4f")
with b2:
    maturity_years = st.number_input("Vencimiento del bono", min_value=1, value=7, step=1, help="Numero de anos hasta el pago final del bono.")
    market_yield = st.number_input("Yield de mercado", min_value=0.0, value=0.048, step=0.005, format="%.4f", help="Tasa de descuento de mercado usada para valorar el bono.")

run_analysis = st.button("Calcular renta fija", type="primary", use_container_width=True)

curve_df = _normalize_curve_columns(pd.DataFrame(curve_inputs))
if CURVE_MATURITY_COL in curve_df.columns and CURVE_YIELD_COL in curve_df.columns:
    curve_df = pd.DataFrame(
        {
            CURVE_MATURITY_COL: pd.to_numeric(curve_df[CURVE_MATURITY_COL], errors="coerce"),
            CURVE_YIELD_COL: pd.to_numeric(curve_df[CURVE_YIELD_COL], errors="coerce"),
        }
    ).dropna()
    maturities = curve_df[CURVE_MATURITY_COL].tolist()
    yields = curve_df[CURVE_YIELD_COL].tolist()
else:
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

seccion("Estructura temporal")
if curve_result:
    params = curve_result["params"]
    curve_shape, slope_bp, curve_implication = _classify_curve_shape(maturities, yields)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tarjeta_kpi("Nivel", format_percent(params["beta0"]), subtexto="Beta 0", help_text="Nivel general de tasas estimado por la curva Nelson-Siegel.")
    with c2:
        tarjeta_kpi("Pendiente", format_percent(params["beta1"]), subtexto="Beta 1", help_text="Diferencia entre tramos cortos y largos de la curva.")
    with c3:
        tarjeta_kpi("Curvatura", format_percent(params["beta2"]), subtexto="Beta 2", help_text="Forma del tramo medio de la estructura temporal.")
    with c4:
        tarjeta_kpi("RMSE", format_number(curve_result["rmse"], decimals=4), subtexto="Error de ajuste", help_text="Error promedio de ajuste entre tasas observadas y curva estimada.")

    s1, s2 = st.columns(2)
    with s1:
        tarjeta_kpi(
            "Forma curva",
            curve_shape,
            subtexto=f"Pendiente corto-largo: {format_number(slope_bp, decimals=1)} pb.",
            help_text="Clasificacion basada en la diferencia entre el vencimiento mas largo y el mas corto disponible.",
        )
    with s2:
        tarjeta_kpi(
            "Puntos FRED",
            str(len(maturities)),
            subtexto="DGS3MO, DGS1, DGS2, DGS5, DGS10 y DGS30 cuando FRED esta disponible.",
        )

    grid = np.linspace(min(maturities), max(maturities), 120)
    fitted = _nelson_siegel_curve(grid, tau=params["tau"], beta0=params["beta0"], beta1=params["beta1"], beta2=params["beta2"])
    observed = pd.DataFrame({"maturity": maturities, "yield": yields}).sort_values("maturity")
    interpolated = np.interp(grid, observed["maturity"].to_numpy(), observed["yield"].to_numpy())

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=maturities, y=yields, mode="markers", name="Observado", marker=dict(size=9)))
    fig.add_trace(go.Scatter(x=grid, y=interpolated, mode="lines", name="Spot interpolada lineal", line=dict(width=2.4, dash="dot")))
    fig.add_trace(go.Scatter(x=grid, y=fitted, mode="lines", name="Nelson-Siegel", line=dict(width=3)))
    plot_card_header("Curva ajustada", "Compara puntos Treasury observados, curva spot interpolada y curva suavizada Nelson-Siegel.", modo=modo)
    st.plotly_chart(
        style_plotly_figure(fig, modo=modo, title="Curva de rendimiento", xaxis_title="Vencimiento en años", yaxis_title="Tasa"),
        use_container_width=True,
    )
    plot_card_footer(curve_implication)
else:
    render_info_card("Curva pendiente", "Ejecuta el cálculo para ver parámetros, ajuste y visualización.")

seccion("Métricas del bono")
if bond_result:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tarjeta_kpi("Precio", format_money(bond_result["price"]), subtexto="Valor teórico")
    with c2:
        tarjeta_kpi("Duración", format_number(bond_result["duration"]), subtexto="Macaulay")
    with c3:
        tarjeta_kpi("Duración mod.", format_number(bond_result["modified_duration"]), subtexto="Sensibilidad")
    with c4:
        tarjeta_kpi("Convexidad", format_number(bond_result["convexity"]), subtexto="Curvatura precio-tasa", help_text="Ajuste de segundo orden de la relacion precio-tasa.")

    render_meta_row(
        {
            "Nominal": format_money(face_value),
            "Cupón": format_percent(coupon_rate),
            "Yield": format_percent(market_yield),
            "Vencimiento": f"{int(maturity_years)} años",
        }
    )

    sensitivity_df = _bond_sensitivity_df(bond_result)
    if not sensitivity_df.empty:
        seccion("Sensibilidad a tasas")
        plot_card_header(
            "Shocks de curva",
            "Compara el cambio de precio ante shocks de +/-50, +/-100 y +/-200 pb usando duracion, duracion + convexidad y repricing exacto.",
            modo=modo,
            caption="La convexidad mejora la aproximacion cuando el movimiento de tasas es grande.",
        )
        st.plotly_chart(
            _build_bond_sensitivity_figure(sensitivity_df, modo=modo),
            use_container_width=True,
        )
        table_df = sensitivity_df.rename(
            columns={
                "shock_bp": "Shock pb",
                "shocked_yield": "Yield shock",
                "price_linear_duration": "Precio lineal D",
                "price_duration_convexity": "Precio D+C",
                "price_exact_reprice": "Precio exacto",
                "pct_change_linear_duration": "Cambio D",
                "pct_change_duration_convexity": "Cambio D+C",
                "pct_change_exact_reprice": "Cambio exacto",
            }
        )
        for col in ["Yield shock", "Cambio D", "Cambio D+C", "Cambio exacto"]:
            if col in table_df.columns:
                table_df[col] = table_df[col].map(format_percent)
        for col in ["Precio lineal D", "Precio D+C", "Precio exacto"]:
            if col in table_df.columns:
                table_df[col] = table_df[col].map(format_money)
        st.dataframe(table_df, use_container_width=True, hide_index=True)
        plot_card_footer(
            "Lectura: ante subidas de tasa el precio cae; la curva exacta muestra la relacion no lineal que la convexidad intenta aproximar."
        )
else:
    render_info_card("Bono pendiente", "Ejecuta el cálculo para obtener precio, duración y convexidad.")

seccion("Lectura ejecutiva")
render_info_card(
    "Uso financiero",
    (
        "Nelson-Siegel resume nivel, pendiente y curvatura de la estructura temporal. "
        "La duración modificada estima la pérdida porcentual aproximada ante un aumento de 100 pb en la tasa."
    ),
)
if curve_result and bond_result:
    params = curve_result["params"]
    duration_loss = bond_result["modified_duration"] * 0.01
    nota(
        f"Con una duración modificada de {format_number(bond_result['modified_duration'])}, un alza de 100 pb implicaría "
        f"una pérdida aproximada de {format_percent(duration_loss)} antes de ajustar por convexidad. "
        f"El nivel estimado de la curva es {format_percent(params['beta0'])}."
    )
