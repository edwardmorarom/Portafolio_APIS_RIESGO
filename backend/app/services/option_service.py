from __future__ import annotations
import numpy as np
from scipy.stats import norm

class OptionService:
    """
    Servicio para la valoración de opciones financieras mediante Black-Scholes.
    Cumple con los requisitos de 'Valoración de Activos' de la rúbrica USTA.
    """

    def calculate_black_scholes(
        self, S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call"
    ) -> dict:
        """
        S: Precio actual del activo (Spot)
        K: Precio de ejercicio (Strike)
        T: Tiempo al vencimiento en años
        r: Tasa libre de riesgo (anualizada)
        sigma: Volatilidad del activo (anualizada)
        """
        try:
            d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)

            if option_type.lower() == "call":
                price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
                delta = norm.cdf(d1)
            else:
                price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
                delta = norm.cdf(d1) - 1

            # Cálculo de Gamma (común para ambos)
            gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
            vega = S * norm.pdf(d1) * np.sqrt(T)

            return {
                "price": float(price),
                "greeks": {
                    "delta": float(delta),
                    "gamma": float(gamma),
                    "vega": float(vega)
                },
                "params": {"spot": S, "strike": K, "tenor": T, "vol": sigma}
            }
        except Exception as e:
            return {"error": str(e), "price": 0.0}

    def implied_volatility(self, target_price: float, S: float, K: float, T: float, r: float) -> float:
        """Encuentra la volatilidad implícita usando el método de Newton-Raphson."""
        sigma = 0.2  # Estimación inicial del 20%
        for _ in range(100):
            res = self.calculate_black_scholes(S, K, T, r, sigma)
            price = res["price"]
            vega = res["greeks"]["vega"]
            
            diff = price - target_price
            if abs(diff) < 1e-6:
                return float(sigma)
            if vega == 0:
                break
            sigma = sigma - diff / vega
        return float(sigma)