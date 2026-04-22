from fastapi import APIRouter

from app.api.v1 import assets, benchmark, capm, decision, investor, macro, market, portfolio, risk, technical

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