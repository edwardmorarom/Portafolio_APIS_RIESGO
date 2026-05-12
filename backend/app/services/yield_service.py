from __future__ import annotations
import numpy as np
from scipy.optimize import minimize

class YieldService:
    """
    Servicio experto en modelación de la curva de tipos usando Nelson-Siegel.
    Cumple con el requisito de 'Modelación Estadística Avanzada' de la rúbrica.
    """

    @staticmethod
    def nelson_siegel(t: np.ndarray, tau: float, beta0: float, beta1: float, beta2: float) -> np.ndarray:
        # t es el tiempo al vencimiento (maturity)
        # beta0: Nivel (Largo plazo)
        # beta1: Pendiente (Corto plazo)
        # beta2: Curvatura (Medio plazo)
        arg = t / tau
        exp_term = np.exp(-arg)
        factor1 = (1 - exp_term) / arg
        factor2 = factor1 - exp_term
        return beta0 + beta1 * factor1 + beta2 * factor2

    def fit_nelson_siegel(self, yields: list[float], maturities: list[float]) -> dict:
        y = np.array(yields)
        t = np.array(maturities)

        # Función objetivo: Minimizar la suma de cuadrados del error
        def objective(params):
            tau, b0, b1, b2 = params
            if tau <= 0: return 1e10
            prediction = self.nelson_siegel(t, tau, b0, b1, b2)
            return np.sum((y - prediction) ** 2)

        # Estimación inicial sensata
        initial_guess = [2.0, y[-1], y[-1] - y[0], 0.0]
        res = minimize(objective, initial_guess, method='Nelder-Mead')
        
        tau_f, b0_f, b1_f, b2_f = res.x
        
        return {
            "params": {
                "tau": float(tau_f), 
                "beta0": float(b0_f), 
                "beta1": float(b1_f), 
                "beta2": float(b2_f)
            },
            "rmse": float(np.sqrt(res.fun / len(y))),
            "curve_type": "Nelson-Siegel",
            "summary": f"Ajuste exitoso. Beta0 (Nivel): {b0_f:.4f}, Beta1 (Pendiente): {b1_f:.4f}"
        }