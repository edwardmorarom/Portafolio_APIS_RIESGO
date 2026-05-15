from __future__ import annotations
import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime, timedelta
from app.services.portfolio_service import PortfolioOptimizerSingleton
from app.clients.market_client import MarketClient

logger = logging.getLogger(__name__)

class RoboAdvisorService:
    def __init__(self, market_client: MarketClient):
        self.cache_file = "roboadvisor_cache.csv"
        self.market_client = market_client

    def suggest_hybrid_portfolio(self, profile: str, total_assets: int, custom_tickers: list[str] = None) -> dict:
        """
        Arma un portafolio mezclando activos sugeridos de la reserva (caché) 
        con los activos específicos que el cliente haya elegido (on-demand).
        """
        if custom_tickers is None:
            custom_tickers = []
            
        custom_tickers = [t.upper() for t in custom_tickers]

        # 1. Cargar la Reserva de 200 activos (Calculada a las 7 AM)
        if not os.path.exists(self.cache_file):
            raise ValueError("La reserva base no está lista. Se requiere ejecutar la tarea de actualización de mercado.")
        
        df_base = pd.read_csv(self.cache_file, index_col=0, parse_dates=True)
        returns_base = df_base.pct_change().dropna()

        # 2. Clasificar la reserva según el Perfil del Inversor
        mean_ret = returns_base.mean() * 252
        volatility = returns_base.std() * np.sqrt(252)

        if profile.lower() == "conservador":
            ranked = volatility.sort_values(ascending=True) # Menor riesgo
        elif profile.lower() == "agresivo":
            ranked = mean_ret.sort_values(ascending=False)  # Mayor retorno
        else: # moderado
            sharpe = mean_ret / volatility
            ranked = sharpe.sort_values(ascending=False)    # Mejor equilibrio

        # 3. Filtrar los activos sugeridos restando los que el usuario ya eligió
        num_auto_assets = max(0, total_assets - len(custom_tickers))
        
        # Evitar sugerir un activo que el usuario ya puso manualmente
        available_for_suggestion = ranked[~ranked.index.isin(custom_tickers)]
        selected_auto_tickers = available_for_suggestion.head(num_auto_assets).index.tolist()

        # 4. Fusión Híbrida: Sugeridos + Capricho del cliente
        final_tickers = list(set(selected_auto_tickers + custom_tickers))

        if len(final_tickers) < 2:
            raise ValueError("Se requieren al menos 2 activos para optimizar un portafolio.")

        # 5. Enviar al Optimizador Singleton
        end_date = df_base.index[-1].strftime("%Y-%m-%d")
        # Cambiamos a 5 años (365 * 5 = 1825 días) para aprovechar la base de datos completa
        start_date = (df_base.index[-1] - timedelta(days=1825)).strftime("%Y-%m-%d")

        optimizer = PortfolioOptimizerSingleton(client=self.market_client)
        optimization_result = optimizer.optimize_markowitz(
            tickers=final_tickers,
            start=start_date,
            end=end_date
        )

        return {
            "profile": profile,
            "total_assets_optimized": len(final_tickers),
            "system_suggested": selected_auto_tickers,
            "user_custom": custom_tickers,
            "markowitz_result": optimization_result
        }