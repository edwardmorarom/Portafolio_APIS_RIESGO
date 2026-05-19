from __future__ import annotations

from typing import Dict, List

import numpy as np
from scipy.optimize import minimize


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

        return {
            "price": float(price),
            "duration": float(macaulay_duration),
            "modified_duration": float(modified_duration),
            "convexity": float(convexity),
        }
