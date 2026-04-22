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


def get_decision_service() -> DecisionService:
    return DecisionService()


def get_capm_service(
    market_client: MarketClient = Depends(get_market_client),
    macro_service: MacroService = Depends(get_macro_service),
) -> CapmService:
    return CapmService(market_client=market_client, macro_service=macro_service)