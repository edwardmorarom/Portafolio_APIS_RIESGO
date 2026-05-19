from __future__ import annotations

import numpy as np
from scipy.stats import norm


class OptionService:
    """
    Servicio para valoracion de opciones europeas mediante Black-Scholes.
    """

    def calculate_black_scholes(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = "call",
    ) -> dict:
        try:
            option_type = option_type.lower()

            d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)

            gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
            vega = S * norm.pdf(d1) * np.sqrt(T)

            if option_type == "call":
                price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
                delta = norm.cdf(d1)
                theta = (
                    -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                    - r * K * np.exp(-r * T) * norm.cdf(d2)
                )
                rho = K * T * np.exp(-r * T) * norm.cdf(d2)
            elif option_type == "put":
                price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
                delta = norm.cdf(d1) - 1
                theta = (
                    -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                    + r * K * np.exp(-r * T) * norm.cdf(-d2)
                )
                rho = -K * T * np.exp(-r * T) * norm.cdf(-d2)
            else:
                return {"error": "option_type debe ser call o put", "price": 0.0}

            return {
                "price": float(price),
                "greeks": {
                    "delta": float(delta),
                    "gamma": float(gamma),
                    "vega": float(vega),
                    "theta": float(theta),
                    "rho": float(rho),
                },
                "params": {
                    "spot": float(S),
                    "strike": float(K),
                    "tenor": float(T),
                    "rate": float(r),
                    "vol": float(sigma),
                },
            }
        except Exception as e:
            return {"error": str(e), "price": 0.0}

    def implied_volatility(
        self,
        target_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: str = "call",
    ) -> float:
        sigma = 0.2

        for _ in range(100):
            result = self.calculate_black_scholes(S, K, T, r, sigma, option_type)
            price = result["price"]
            vega = result["greeks"]["vega"]

            diff = price - target_price

            if abs(diff) < 1e-6:
                return float(sigma)

            if abs(vega) < 1e-12:
                break

            sigma = max(1e-6, sigma - diff / vega)

        return float(sigma)
