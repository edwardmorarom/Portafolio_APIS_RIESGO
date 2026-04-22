from fastapi import Depends

from app.clients.macro_client import MacroClient
from app.clients.market_client import MarketClient
from app.core.settings import Settings, get_settings
from app.services.decision_service import DecisionService
from app.services.macro_service import MacroService
from app.services.market_service import MarketService
from app.services.portfolio_service import PortfolioService
from app.services.risk_service import RiskService
from app.services.technical_service import TechnicalService
from app.services.capm_service import CapmService
from app.services.decision_service import DecisionService
from app.services.investor_service import InvestorService
from app.services.assets_service import AssetsService
from app.services.benchmark_service import BenchmarkService
from app.services.help_service import HelpService
from app.services.returns_stats_service import ReturnsStatsService

def get_app_settings() -> Settings:
    return get_settings()


def get_market_client(settings: Settings = Depends(get_app_settings)) -> MarketClient:
    return MarketClient(settings=settings)


def get_macro_client(settings: Settings = Depends(get_app_settings)) -> MacroClient:
    return MacroClient(settings=settings)


def get_market_service(client: MarketClient = Depends(get_market_client)) -> MarketService:
    return MarketService(client=client)


def get_technical_service(client: MarketClient = Depends(get_market_client)) -> TechnicalService:
    return TechnicalService(client=client)


def get_risk_service(client: MarketClient = Depends(get_market_client)) -> RiskService:
    return RiskService(client=client)


def get_portfolio_service(client: MarketClient = Depends(get_market_client)) -> PortfolioService:
    return PortfolioService(client=client)


def get_macro_service(client: MacroClient = Depends(get_macro_client)) -> MacroService:
    return MacroService(client=client)


def get_capm_service(
    market_client: MarketClient = Depends(get_market_client),
    macro_service: MacroService = Depends(get_macro_service),
) -> CapmService:
    return CapmService(market_client=market_client, macro_service=macro_service)


def get_decision_service(
    risk_service: RiskService = Depends(get_risk_service),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    capm_service: CapmService = Depends(get_capm_service),
) -> DecisionService:
    return DecisionService(
        risk_service=risk_service,
        portfolio_service=portfolio_service,
        capm_service=capm_service,
    )


def get_investor_service() -> InvestorService:
    return InvestorService()


def get_assets_service() -> AssetsService:
    return AssetsService()


def get_benchmark_service(
    market_client: MarketClient = Depends(get_market_client),
    macro_service: MacroService = Depends(get_macro_service),
) -> BenchmarkService:
    return BenchmarkService(market_client=market_client, macro_service=macro_service)


def get_help_service() -> HelpService:
    return HelpService()


def get_returns_stats_service(client: MarketClient = Depends(get_market_client)) -> ReturnsStatsService:
    return ReturnsStatsService(client=client)