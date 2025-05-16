from fastapi import APIRouter

from src.api.routes.v1.metrics.popular_models import \
    router as popular_models_router

router = APIRouter(prefix="/v1/metrics", tags=["metrics"])

router.include_router(
    popular_models_router, prefix="/popular_models", tags=["popular_models"]
)
