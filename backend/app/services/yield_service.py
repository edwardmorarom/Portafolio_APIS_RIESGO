from __future__ import annotations

from datetime import date
from typing import Dict, List

import numpy as np
from scipy.optimize import minimize

from app.schemas.fixed_income import BondPurchaseRequest


class YieldService:
    """
    Servicio experto en modelacion de curva Nelson-Siegel y metricas de renta fija.
    """

    @staticmethod
    def nelson_siegel(
        t: np.ndarray,
        tau: float,
        beta0: float,
        beta1: float,
        beta2: float,
    ) -> np.ndarray:
        arg = t / tau
        exp_term = np.exp(-arg)

        factor1 = (1 - exp_term) / arg
        factor2 = factor1 - exp_term

        return beta0 + beta1 * factor1 + beta2 * factor2

    def fit_nelson_siegel(
        self,
        yields: List[float],
        maturities: List[float],
    ) -> dict:
        y = np.array(yields)
        t = np.array(maturities)

        def objective(params):
            tau, b0, b1, b2 = params

            if tau <= 0:
                return 1e10

            prediction = self.nelson_siegel(t, tau, b0, b1, b2)

            return np.sum((y - prediction) ** 2)

        initial_guess = [2.0, y[-1], y[-1] - y[0], 0.0]

        result = minimize(
            objective,
            initial_guess,
            method="Nelder-Mead",
        )

        tau_f, b0_f, b1_f, b2_f = result.x

        return {
            "params": {
                "tau": float(tau_f),
                "beta0": float(b0_f),
                "beta1": float(b1_f),
                "beta2": float(b2_f),
            },
            "rmse": float(np.sqrt(result.fun / len(y))),
            "curve_type": "Nelson-Siegel",
            "summary": (
                f"Ajuste exitoso. "
                f"Nivel={b0_f:.4f}, "
                f"Pendiente={b1_f:.4f}, "
                f"Curvatura={b2_f:.4f}"
            ),
        }

    def calculate_bond_metrics(
        self,
        face_value: float,
        coupon_rate: float,
        maturity_years: int,
        market_yield: float,
    ) -> Dict[str, float]:
        """
        Calcula precio, duracion Macaulay,
        duracion modificada y convexidad.
        """

        coupon = face_value * coupon_rate

        cashflows = []

        for t in range(1, maturity_years + 1):
            cf = coupon

            if t == maturity_years:
                cf += face_value

            cashflows.append((t, cf))

        price = sum(
            cf / ((1 + market_yield) ** t)
            for t, cf in cashflows
        )

        macaulay_duration = (
            sum(
                t * cf / ((1 + market_yield) ** t)
                for t, cf in cashflows
            )
            / price
        )

        modified_duration = macaulay_duration / (1 + market_yield)

        convexity = (
            sum(
                (
                    cf
                    * t
                    * (t + 1)
                    / ((1 + market_yield) ** (t + 2))
                )
                for t, cf in cashflows
            )
            / price
        )

        sensitivity = []
        for shock_bp in [-200, -100, -50, 50, 100, 200]:
            delta_yield = shock_bp / 10000.0
            shocked_yield = max(market_yield + delta_yield, 0.0)
            exact_price = sum(
                cf / ((1 + shocked_yield) ** t)
                for t, cf in cashflows
            )
            linear_price = price * (1.0 - modified_duration * delta_yield)
            convexity_price = price * (
                1.0 - modified_duration * delta_yield + 0.5 * convexity * (delta_yield**2)
            )
            sensitivity.append(
                {
                    "shock_bp": int(shock_bp),
                    "shocked_yield": float(shocked_yield),
                    "price_linear_duration": float(linear_price),
                    "price_duration_convexity": float(convexity_price),
                    "price_exact_reprice": float(exact_price),
                    "pct_change_linear_duration": float((linear_price / price) - 1.0),
                    "pct_change_duration_convexity": float((convexity_price / price) - 1.0),
                    "pct_change_exact_reprice": float((exact_price / price) - 1.0),
                }
            )

        return {
            "price": float(price),
            "duration": float(macaulay_duration),
            "modified_duration": float(modified_duration),
            "convexity": float(convexity),
            "sensitivity": sensitivity,
        }

    @staticmethod
    def _add_months(value: date, months: int) -> date:
        month_index = value.month - 1 + months
        year = value.year + month_index // 12
        month = month_index % 12 + 1
        month_lengths = [
            31,
            29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
            31,
            30,
            31,
            30,
            31,
            31,
            30,
            31,
            30,
            31,
        ]
        return date(year, month, min(value.day, month_lengths[month - 1]))

    def _coupon_dates(self, issue_date: date, maturity_date: date, frequency: int) -> list[date]:
        months = 12 // frequency
        dates = [maturity_date]
        cursor = maturity_date
        while True:
            previous = self._add_months(cursor, -months)
            if previous <= issue_date:
                break
            dates.append(previous)
            cursor = previous
        return sorted(dates)

    def _coupon_window(
        self,
        issue_date: date,
        maturity_date: date,
        settlement_date: date,
        frequency: int,
    ) -> tuple[date, date]:
        previous = issue_date
        for payment_date in self._coupon_dates(issue_date, maturity_date, frequency):
            if settlement_date < payment_date:
                return previous, payment_date
            previous = payment_date
        raise ValueError("No hay cupon pendiente para la fecha de negociacion enviada.")

    def _future_cashflows(
        self,
        issue_date: date,
        maturity_date: date,
        settlement_date: date,
        face_value: float,
        coupon_rate: float,
        frequency: int,
        market_yield: float,
    ) -> list[dict]:
        coupon_per_period = face_value * coupon_rate / frequency
        cashflows = []
        for payment_date in self._coupon_dates(issue_date, maturity_date, frequency):
            if payment_date <= settlement_date:
                continue
            days = (payment_date - settlement_date).days
            time_years = days / 365.0
            cashflow = coupon_per_period + (face_value if payment_date == maturity_date else 0.0)
            discount_factor = 1.0 / ((1.0 + (market_yield / frequency)) ** (time_years * frequency))
            cashflows.append(
                {
                    "payment_date": payment_date,
                    "days": int(days),
                    "time_years": float(time_years),
                    "cashflow": float(cashflow),
                    "discount_factor": float(discount_factor),
                    "present_value": float(cashflow * discount_factor),
                }
            )
        return cashflows

    def _price_from_cashflows(self, cashflows: list[dict], periodic_yield: float) -> float:
        return float(
            sum(
                float(item["cashflow"])
                / ((1.0 + periodic_yield) ** float(item["period"]))
                for item in cashflows
            )
        )

    @staticmethod
    def _periodic_rate(annual_rate: float, rate_type: str, frequency: int) -> float:
        if rate_type == "nominal_anual":
            return annual_rate / frequency
        if rate_type == "efectiva_anual":
            return (1.0 + annual_rate) ** (1.0 / frequency) - 1.0
        raise ValueError("tipo de tasa invalido")

    def calculate_bond_purchase(self, request: BondPurchaseRequest) -> dict:
        coupon_periodic_rate = self._periodic_rate(
            annual_rate=request.coupon_rate,
            rate_type=request.coupon_rate_type,
            frequency=request.coupon_frequency,
        )
        market_yield_periodic = self._periodic_rate(
            annual_rate=request.market_yield,
            rate_type=request.market_yield_type,
            frequency=request.coupon_frequency,
        )
        previous_coupon, next_coupon = self._coupon_window(
            issue_date=request.issue_date,
            maturity_date=request.maturity_date,
            settlement_date=request.settlement_date,
            frequency=request.coupon_frequency,
        )
        coupon_period_days = max((next_coupon - previous_coupon).days, 1)
        accrued_days = max((request.settlement_date - previous_coupon).days, 0)
        coupon_per_period = request.face_value * coupon_periodic_rate
        accrued_interest = coupon_per_period * min(accrued_days / coupon_period_days, 1.0)

        clean_price_value = request.face_value * request.clean_price_pct / 100.0
        dirty_price = clean_price_value + accrued_interest
        fees = (dirty_price * request.fees_pct / 100.0) + request.fixed_fee
        total_purchase = dirty_price + fees

        cashflows = []
        period = 1
        for payment_date in self._coupon_dates(
            issue_date=request.issue_date,
            maturity_date=request.maturity_date,
            frequency=request.coupon_frequency,
        ):
            if payment_date <= request.settlement_date:
                continue

            cashflow = coupon_per_period + (request.face_value if payment_date == request.maturity_date else 0.0)
            discount_factor = 1.0 / ((1.0 + market_yield_periodic) ** period)
            cashflows.append(
                {
                    "payment_date": payment_date,
                    "days_from_settlement": int((payment_date - request.settlement_date).days),
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
        buyer_npv = theoretical_price - total_purchase
        macaulay_duration = float(
            sum((item["period"] / request.coupon_frequency) * item["present_value"] for item in cashflows)
            / theoretical_price
        )
        modified_duration = macaulay_duration / (1.0 + market_yield_periodic)

        periodic_yield_down = self._periodic_rate(
            annual_rate=max(request.market_yield - 0.0001, 0.0),
            rate_type=request.market_yield_type,
            frequency=request.coupon_frequency,
        )
        periodic_yield_up = self._periodic_rate(
            annual_rate=request.market_yield + 0.0001,
            rate_type=request.market_yield_type,
            frequency=request.coupon_frequency,
        )
        price_down = self._price_from_cashflows(cashflows, periodic_yield_down)
        price_up = self._price_from_cashflows(cashflows, periodic_yield_up)
        dv01 = max(0.0, (price_down - price_up) / 2.0)
        dv01_approx = modified_duration * theoretical_price * 0.0001
        interpretation = (
            "La compra luce favorable frente al yield ingresado: el precio teorico supera el total pagado."
            if theoretical_price > total_purchase
            else "La compra exige cautela: el comprador estaria pagando caro frente al yield ingresado."
        )

        return {
            "position": "purchase",
            "inputs": {
                "issue_date": request.issue_date,
                "maturity_date": request.maturity_date,
                "settlement_date": request.settlement_date,
                "face_value": float(request.face_value),
                "coupon_rate": float(request.coupon_rate),
                "coupon_rate_type": request.coupon_rate_type,
                "coupon_frequency": int(request.coupon_frequency),
                "market_yield": float(request.market_yield),
                "market_yield_type": request.market_yield_type,
                "clean_price_pct": float(request.clean_price_pct),
                "fees_pct": float(request.fees_pct),
                "fixed_fee": float(request.fixed_fee),
                "currency": request.currency.upper(),
            },
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
                "buyer_npv": float(buyer_npv),
                "remaining_periods": int(len(cashflows)),
                "macaulay_duration": float(macaulay_duration),
                "modified_duration": float(modified_duration),
                "dv01": float(dv01),
                "dv01_approx": float(dv01_approx),
            },
            "cashflows": cashflows,
            "interpretation": interpretation,
        }
