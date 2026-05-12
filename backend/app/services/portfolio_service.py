from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from app.clients.market_client import MarketClient

class PortfolioOptimizerSingleton:
    """
    Implementación del patrón Singleton para el Optimizador de Portafolios.
    Mantiene en caché la matriz de covarianzas para evitar recálculos costosos.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PortfolioOptimizerSingleton, cls).__new__(cls)
            cls._instance._cache = {}  # Diccionario para caché
        return cls._instance

    def __init__(self, client: MarketClient = None):
        if not hasattr(self, 'initialized'):
            self.client = client
            self.initialized = True

    def _get_returns_matrix(self, tickers: list[str], start: str, end: str) -> pd.DataFrame:
        """Descarga y alinea los rendimientos de múltiples activos."""
        cache_key = f"{','.join(sorted(tickers))}_{start}_{end}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        df_list = []
        for ticker in tickers:
            df = self.client.get_prices(ticker, start, end)
            if not df.empty and "Close" in df.columns:
                ret = df["Close"].pct_change().dropna()
                ret.name = ticker
                df_list.append(ret)
        
        if not df_list:
            raise ValueError("No se pudieron obtener datos para los tickers solicitados.")
            
        returns_matrix = pd.concat(df_list, axis=1).dropna()
        self._cache[cache_key] = returns_matrix  # Guardar en caché
        return returns_matrix

    def optimize_markowitz(self, tickers: list[str], start: str, end: str, target_return: float = None) -> dict:
        """
        Optimiza el portafolio minimizando la varianza (riesgo).
        Si target_return se especifica, minimiza la varianza para ese retorno objetivo.
        """
        returns = self._get_returns_matrix(tickers, start, end)
        mean_returns = returns.mean() * 252  # Anualizado
        cov_matrix = returns.cov() * 252     # Anualizado
        num_assets = len(tickers)

        # Función objetivo: Minimizar Volatilidad (Riesgo)
        def portfolio_volatility(weights):
            return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

        # Restricción 1: Los pesos deben sumar 1 (100% invertido)
        constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        
        # Restricción 2 (Opcional): Retorno objetivo
        if target_return is not None:
            constraints.append({
                'type': 'eq', 'fun': lambda x: np.sum(mean_returns * x) - target_return
            })

        # Límites: No posiciones cortas (0 <= peso <= 1)
        bounds = tuple((0.0, 1.0) for _ in range(num_assets))
        
        # Peso inicial equitativo
        init_guess = num_assets * [1. / num_assets,]

        # Optimización
        optimized = minimize(portfolio_volatility, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)

        opt_weights = optimized.x
        opt_return = np.sum(mean_returns * opt_weights)
        opt_risk = optimized.fun
        sharpe_ratio = opt_return / opt_risk if opt_risk > 0 else 0

        return {
            "weights": {tickers[i]: float(opt_weights[i]) for i in range(num_assets)},
            "expected_return_annual": float(opt_return),
            "volatility_annual": float(opt_risk),
            "sharpe_ratio": float(sharpe_ratio),
            "optimization_status": optimized.message
        }