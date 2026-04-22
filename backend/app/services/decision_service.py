from __future__ import annotations

from app.services.capm_service import CapmService
from app.services.portfolio_service import PortfolioService
from app.services.risk_service import RiskService


class DecisionService:
    def __init__(
        self,
        risk_service: RiskService,
        portfolio_service: PortfolioService,
        capm_service: CapmService,
    ) -> None:
        self.risk_service = risk_service
        self.portfolio_service = portfolio_service
        self.capm_service = capm_service

    def _infer_stance(self, portfolio_beta: float, alpha_simple: float, mc_var_daily: float) -> str:
        if portfolio_beta < 0.9 and mc_var_daily < 0.02:
            return "conservadora"
        if portfolio_beta > 1.1 or mc_var_daily > 0.03:
            return "agresiva"
        return "neutral"

    def build_panel(
        self,
        tickers: list[str],
        weights: list[float],
        benchmark_ticker: str,
        base_currency: str,
        start: str,
        end: str,
        alpha: float,
        n_sim: int,
        n_portfolios: int,
        return_type: str,
    ) -> dict:
        risk = self.risk_service.calculate_var(
            tickers=tickers,
            weights=weights,
            start=start,
            end=end,
            alpha=alpha,
            n_sim=n_sim,
            return_type=return_type,
        )

        frontier = self.portfolio_service.build_efficient_frontier(
            tickers=tickers,
            start=start,
            end=end,
            rf_annual=0.04,
            n_portfolios=n_portfolios,
            return_type=return_type,
        )

        capm = self.capm_service.calculate_portfolio_capm(
            tickers=tickers,
            weights=weights,
            benchmark_ticker=benchmark_ticker,
            base_currency=base_currency,
            start=start,
            end=end,
            return_type=return_type,
        )

        stance = self._infer_stance(
            portfolio_beta=capm["portfolio_beta"],
            alpha_simple=capm["alpha_simple"],
            mc_var_daily=risk["monte_carlo"]["var_daily"],
        )

        summary = (
            f"Portafolio en postura {stance}. "
            f"Beta={capm['portfolio_beta']:.3f}, "
            f"alpha={capm['alpha_simple']:.3%}, "
            f"VaR MC diario={risk['monte_carlo']['var_daily']:.3%}."
        )

        return {
            "tickers": tickers,
            "weights": weights,
            "benchmark_ticker": capm["benchmark_ticker"],
            "base_currency": capm["base_currency"],
            "rf_ticker": capm["rf_ticker"],
            "rf_rate_pct": capm["rf_rate_pct"],
            "portfolio_beta": capm["portfolio_beta"],
            "portfolio_return_annual": capm["portfolio_return_annual"],
            "benchmark_return_annual": capm["benchmark_return_annual"],
            "capm_expected_return": capm["capm_expected_return"],
            "alpha_simple": capm["alpha_simple"],
            "historical_var_daily": risk["historical"]["var_daily"],
            "historical_cvar_daily": risk["historical"]["cvar_daily"],
            "monte_carlo_var_daily": risk["monte_carlo"]["var_daily"],
            "monte_carlo_cvar_daily": risk["monte_carlo"]["cvar_daily"],
            "min_variance_return": frontier["min_variance"]["return"],
            "max_sharpe_return": frontier["max_sharpe"]["return"],
            "stance": stance,
            "summary": summary,
            "start": start,
            "end": end,
        }