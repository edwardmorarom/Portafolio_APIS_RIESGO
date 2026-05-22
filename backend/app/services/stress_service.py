from __future__ import annotations


class StressTester:
    FIXED_INCOME_DURATION_PROXY = {
        "TIP": 6.7,
        "SPIP": 5.0,
        "MUB": 5.8,
        "BNDX": 7.0,
        "BKLN": 0.4,
        "AGG": 6.0,
        "BND": 6.1,
        "IEF": 7.4,
        "TLT": 16.5,
        "SHY": 1.9,
        "LQD": 8.4,
        "HYG": 3.6,
    }

    def __init__(
        self,
        portfolio_value: float,
        portfolio: list[dict],
        expected_return: float,
        volatility: float,
        var_parametric_99: float | None = None,
        var_monte_carlo_99: float | None = None,
    ) -> None:
        self.portfolio_value = float(portfolio_value)
        self.portfolio = self._normalize_portfolio(portfolio)
        self.expected_return = float(expected_return)
        self.volatility = float(volatility)
        self.var_parametric_99 = (
            abs(float(var_parametric_99))
            if var_parametric_99 is not None
            else self._parametric_var_99(self.expected_return, self.volatility)
        )
        self.var_monte_carlo_99 = (
            abs(float(var_monte_carlo_99))
            if var_monte_carlo_99 is not None
            else self._monte_carlo_proxy_var_99(self.expected_return, self.volatility)
        )

    @staticmethod
    def _normalize_portfolio(portfolio: list[dict]) -> list[dict]:
        total = sum(float(asset.get("weight", 0.0)) for asset in portfolio)
        if total <= 0:
            raise ValueError("La suma de pesos debe ser mayor que 0")

        normalized = []
        for asset in portfolio:
            normalized.append(
                {
                    "ticker": str(asset.get("ticker", "")).strip().upper(),
                    "weight": float(asset.get("weight", 0.0)) / total,
                    "beta": float(asset.get("beta", 1.0)),
                    "duration": asset.get("duration"),
                    "convexity": asset.get("convexity"),
                }
            )
        return normalized

    @staticmethod
    def _parametric_var_99(expected_return: float, volatility: float) -> float:
        z_99 = 2.3263478740408408
        return float(max(0.0, z_99 * volatility - expected_return))

    @staticmethod
    def _monte_carlo_proxy_var_99(expected_return: float, volatility: float) -> float:
        # Deterministic proxy for a 99% Monte Carlo tail, avoiding random API responses.
        z_tail = 2.5758293035489004
        return float(max(0.0, z_tail * volatility - expected_return))

    @staticmethod
    def _duration_proxy(ticker: str) -> float | None:
        normalized = ticker.strip().upper()
        return StressTester.FIXED_INCOME_DURATION_PROXY.get(normalized)

    @staticmethod
    def _rate_reprice_pct(asset: dict, rate_shock_bp: int) -> float:
        dr = float(rate_shock_bp) / 10_000.0
        if dr == 0:
            return 0.0

        duration = asset.get("duration")
        convexity = asset.get("convexity")
        if duration is None:
            duration = StressTester._duration_proxy(str(asset.get("ticker", "")))
            if duration is None:
                return 0.0

        duration = float(duration)
        convexity = 0.0 if convexity is None else float(convexity)
        return float((-duration * dr) + (0.5 * convexity * dr**2))

    def apply(self, scenario: dict) -> dict:
        name = str(scenario.get("name") or "Escenario")
        rate_shock_bp = int(scenario.get("rate_shock_bp", 0))
        market_drop_pct = float(scenario.get("market_drop_pct", 0.0))
        vol_multiplier = float(scenario.get("vol_multiplier", 1.0))

        asset_impacts = []
        portfolio_return = 0.0
        for asset in self.portfolio:
            market_impact = float(asset["beta"]) * market_drop_pct
            rate_impact = self._rate_reprice_pct(asset, rate_shock_bp)
            price_change_pct = market_impact + rate_impact
            contribution_pct = float(asset["weight"]) * price_change_pct
            portfolio_return += contribution_pct
            asset_impacts.append(
                {
                    "ticker": asset["ticker"],
                    "weight": float(asset["weight"]),
                    "beta": float(asset["beta"]),
                    "price_change_pct": float(price_change_pct),
                    "contribution_pct": float(contribution_pct),
                }
            )

        loss_pct = max(0.0, -portfolio_return)
        loss_amount = self.portfolio_value * loss_pct
        stressed_volatility = self.volatility * vol_multiplier
        stressed_var_parametric_99 = self._parametric_var_99(
            self.expected_return + portfolio_return,
            stressed_volatility,
        )
        stressed_var_monte_carlo_99 = self._monte_carlo_proxy_var_99(
            self.expected_return + portfolio_return,
            stressed_volatility,
        )
        stressed_value = max(0.0, self.portfolio_value - loss_amount)
        severity = StressTestingService().classify_severity(loss_pct)

        interpretation = (
            f"{name}: perdida puntual estimada de {loss_pct:.2%}; "
            f"VaR parametrico 99% pasa de {self.var_parametric_99:.2%} a {stressed_var_parametric_99:.2%}."
        )

        return {
            "scenario_name": name,
            "loss_pct": float(loss_pct),
            "loss_amount": float(loss_amount),
            "stressed_portfolio_value": float(stressed_value),
            "stressed_volatility": float(stressed_volatility),
            "stressed_var_parametric_99": float(stressed_var_parametric_99),
            "stressed_var_monte_carlo_99": float(stressed_var_monte_carlo_99),
            "severity": severity,
            "asset_impacts": asset_impacts,
            "interpretation": interpretation,
        }

    def run(self, scenarios: list[dict]) -> dict:
        return {
            "base_metrics": {
                "portfolio_value": self.portfolio_value,
                "expected_return": self.expected_return,
                "volatility": self.volatility,
                "var_parametric_99": self.var_parametric_99,
                "var_monte_carlo_99": self.var_monte_carlo_99,
            },
            "stressed_metrics": [self.apply(scenario) for scenario in scenarios],
        }


class StressTestingService:
    def classify_severity(self, estimated_loss_pct: float) -> str:
        if estimated_loss_pct < 0.05:
            return "bajo"
        if estimated_loss_pct < 0.15:
            return "moderado"
        if estimated_loss_pct < 0.30:
            return "alto"
        return "critico"

    def run_scenario(
        self,
        portfolio_value: float,
        expected_return: float,
        volatility: float,
        var_95: float,
        beta: float,
        rate_shock: float = 0.0,
        market_shock: float = 0.0,
        benchmark_shock: float | None = None,
        volatility_multiplier: float = 1.0,
    ) -> dict:
        stressed_return = expected_return + (beta * market_shock) - rate_shock
        stressed_volatility = volatility * volatility_multiplier
        stressed_var_95 = abs(var_95) * volatility_multiplier + max(0.0, -market_shock * beta)

        estimated_loss_pct = max(0.0, -stressed_return) + stressed_var_95
        estimated_loss = portfolio_value * estimated_loss_pct
        stressed_portfolio_value = max(0.0, portfolio_value - estimated_loss)

        severity = self.classify_severity(estimated_loss_pct)
        benchmark_reference = market_shock if benchmark_shock is None else benchmark_shock
        benchmark_loss_pct = max(0.0, -float(benchmark_reference))

        relative_to_benchmark = (
            "mejor defensa que el benchmark"
            if estimated_loss_pct < benchmark_loss_pct
            else "menor eficiencia defensiva que el benchmark"
        )
        if benchmark_loss_pct == 0 and estimated_loss_pct == 0:
            relative_to_benchmark = "impacto similar al benchmark"

        if estimated_loss_pct < 0.05:
            interpretation = "La perdida bajo estres es baja; el portafolio muestra resistencia relativa."
        elif estimated_loss_pct < 0.15:
            interpretation = "La perdida bajo estres es moderada; conviene monitorear exposicion ante shocks adversos."
        else:
            interpretation = "La perdida bajo estres es alta; existe exposicion relevante ante escenarios adversos."

        if relative_to_benchmark == "mejor defensa que el benchmark":
            interpretation += " Ademas, cae menos que el benchmark y muestra mejor comportamiento defensivo relativo."
        elif relative_to_benchmark == "menor eficiencia defensiva que el benchmark":
            interpretation += " Ademas, cae mas que el benchmark y pierde eficiencia defensiva relativa."

        summary = (
            f"Escenario de stress {severity}: perdida estimada "
            f"{estimated_loss_pct:.2%} sobre un portafolio de {portfolio_value:,.2f}."
        )

        return {
            "base_portfolio_value": float(portfolio_value),
            "stressed_return": float(stressed_return),
            "stressed_volatility": float(stressed_volatility),
            "stressed_var_95": float(stressed_var_95),
            "estimated_loss_pct": float(estimated_loss_pct),
            "estimated_loss": float(estimated_loss),
            "stressed_portfolio_value": float(stressed_portfolio_value),
            "benchmark_loss_pct": float(benchmark_loss_pct),
            "relative_to_benchmark": relative_to_benchmark,
            "severity": severity,
            "interpretation": interpretation,
            "summary": summary,
        }

    def run_stress_test(
        self,
        portfolio_value: float,
        portfolio: list[dict],
        scenarios: list[dict],
        expected_return: float,
        volatility: float,
        var_parametric_99: float | None = None,
        var_monte_carlo_99: float | None = None,
    ) -> dict:
        tester = StressTester(
            portfolio_value=portfolio_value,
            portfolio=portfolio,
            expected_return=expected_return,
            volatility=volatility,
            var_parametric_99=var_parametric_99,
            var_monte_carlo_99=var_monte_carlo_99,
        )
        return tester.run(scenarios)
