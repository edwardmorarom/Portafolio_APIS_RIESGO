from __future__ import annotations

import numpy as np
from scipy.stats import norm


class OptionPricer:
    """
    Servicio para valoracion de opciones europeas mediante Black-Scholes.
    """

    def _d1_d2(self, S: float, K: float, T: float, r: float, sigma: float) -> tuple[float, float]:
        sigma_sqrt_t = sigma * np.sqrt(T)
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / sigma_sqrt_t
        d2 = d1 - sigma_sqrt_t
        return float(d1), float(d2)

    def black_scholes(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = "call",
    ) -> float:
        option_type = option_type.lower()
        d1, d2 = self._d1_d2(S, K, T, r, sigma)

        if option_type == "call":
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        elif option_type == "put":
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        else:
            raise ValueError("option_type debe ser call o put")

        return float(price)

    def greeks(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = "call",
    ) -> dict:
        option_type = option_type.lower()
        d1, d2 = self._d1_d2(S, K, T, r, sigma)

        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        vega = S * norm.pdf(d1) * np.sqrt(T)

        if option_type == "call":
            delta = norm.cdf(d1)
            theta = (
                -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                - r * K * np.exp(-r * T) * norm.cdf(d2)
            )
            rho = K * T * np.exp(-r * T) * norm.cdf(d2)
        elif option_type == "put":
            delta = norm.cdf(d1) - 1
            theta = (
                -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                + r * K * np.exp(-r * T) * norm.cdf(-d2)
            )
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2)
        else:
            raise ValueError("option_type debe ser call o put")

        return {
            "delta": float(delta),
            "gamma": float(gamma),
            "vega": float(vega),
            "theta": float(theta),
            "rho": float(rho),
        }

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
            price = self.black_scholes(S, K, T, r, sigma, option_type)
            greeks = self.greeks(S, K, T, r, sigma, option_type)

            return {
                "price": float(price),
                "greeks": greeks,
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


class OptionService(OptionPricer):
    pass
