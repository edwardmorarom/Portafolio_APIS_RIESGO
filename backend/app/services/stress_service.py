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
        volatility_multiplier: float = 1.0,
    ) -> dict:
        stressed_return = expected_return + (beta * market_shock) - rate_shock
        stressed_volatility = volatility * volatility_multiplier
        stressed_var_95 = abs(var_95) * volatility_multiplier + max(0.0, -market_shock * beta)

        estimated_loss_pct = max(0.0, -stressed_return) + stressed_var_95
        estimated_loss = portfolio_value * estimated_loss_pct
        stressed_portfolio_value = max(0.0, portfolio_value - estimated_loss)

        severity = self.classify_severity(estimated_loss_pct)

        summary = (
            f"Escenario de stress {severity}: perdida estimada "
            f"{estimated_loss_pct:.2%} sobre un portafolio de {portfolio_value:,.2f}."
        )

        return {
            "stressed_return": float(stressed_return),
            "stressed_volatility": float(stressed_volatility),
            "stressed_var_95": float(stressed_var_95),
            "estimated_loss": float(estimated_loss),
            "stressed_portfolio_value": float(stressed_portfolio_value),
            "severity": severity,
            "summary": summary,
        }
