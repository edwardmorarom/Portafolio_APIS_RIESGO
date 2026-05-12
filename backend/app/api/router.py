from fastapi import APIRouter
from app.api.v1 import alerts, assets, benchmark, capm, decision, garch, help, investor, macro, market, portfolio, returns_stats, risk, technical, valuation, roboadvisor


api_router = APIRouter() 

api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
api_router.include_router(market.router, prefix="/market", tags=["Market"])
api_router.include_router(technical.router, prefix="/technical", tags=["Technical"])
api_router.include_router(risk.router, prefix="/risk", tags=["Risk"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
api_router.include_router(macro.router, prefix="/macro", tags=["Macro"])
api_router.include_router(capm.router, prefix="/capm", tags=["CAPM"])
api_router.include_router(decision.router, prefix="/decision", tags=["Decision"])
api_router.include_router(investor.router, prefix="/investor", tags=["Investor"])
api_router.include_router(benchmark.router, prefix="/benchmark", tags=["Benchmark"])
api_router.include_router(help.router, prefix="/help", tags=["Help"])
api_router.include_router(returns_stats.router, prefix="/returns-stats", tags=["ReturnsStats"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(garch.router, prefix="/garch", tags=["GARCH"])
api_router.include_router(valuation.router, prefix="/valuation", tags=["Valoración y Curvas"])
api_router.include_router(roboadvisor.router, prefix="/roboadvisor", tags=["RoboAdvisor"])