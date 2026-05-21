from __future__ import annotations


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
        benchmark_loss_pct = abs(benchmark_shock) if benchmark_shock is not None and benchmark_shock < 0 else None

        relative_to_benchmark = None
        if benchmark_loss_pct is not None:
            relative_to_benchmark = (
                "mejor defensa que el benchmark"
                if estimated_loss_pct < benchmark_loss_pct
                else "menor eficiencia defensiva que el benchmark"
            )

        if estimated_loss_pct < 0.05:
            interpretation = "La pérdida bajo estrés es baja; el portafolio muestra resistencia relativa."
        elif estimated_loss_pct < 0.15:
            interpretation = "La pérdida bajo estrés es moderada; conviene monitorear exposición ante shocks adversos."
        else:
            interpretation = "La pérdida bajo estrés es alta; existe exposición relevante ante escenarios adversos."

        if relative_to_benchmark == "mejor defensa que el benchmark":
            interpretation += " Además, cae menos que el benchmark y muestra mejor comportamiento defensivo relativo."
        elif relative_to_benchmark == "menor eficiencia defensiva que el benchmark":
            interpretation += " Además, cae más que el benchmark y pierde eficiencia defensiva relativa."

        summary = (
            f"Escenario de stress {severity}: pérdida estimada "
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
            "benchmark_loss_pct": float(benchmark_loss_pct) if benchmark_loss_pct is not None else None,
            "relative_to_benchmark": relative_to_benchmark,
            "severity": severity,
            "interpretation": interpretation,
            "summary": summary,
        }
