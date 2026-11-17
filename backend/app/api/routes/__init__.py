from fastapi import APIRouter
from backend.app.api.routes.datasets import router as datasets_router
from backend.app.api.routes.cleaning import router as cleaning_router
from backend.app.api.routes.analytics import router as analytics_router
from backend.app.api.routes.ml import router as ml_router
from backend.app.api.routes.reports import router as reports_router

api_router = APIRouter()
api_router.include_router(datasets_router)
api_router.include_router(cleaning_router)
api_router.include_router(analytics_router)
api_router.include_router(ml_router)
api_router.include_router(reports_router)

__all__ = ["api_router"]
