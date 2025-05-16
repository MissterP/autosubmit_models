from copy import copy
from typing import Optional

from fastapi import APIRouter, Request

from src.api.schemas.popular_models.popular_models_aggregated_response import \
    AggregatedPopularModelsResponse
from src.domain.controllers.tr_popular_models_aggregated import \
    TrPopularModelsAggregated
from src.exceptions.exceptions import ServiceUnavailableException
from src.logging.context import get_current_request_id
from src.logging.logger import ContextualLogger

router = APIRouter()


@router.get("/aggregated", response_model=AggregatedPopularModelsResponse)
async def get_aggregated_popular_models(
    request: Request,
    limit: Optional[int] = None,
):
    """Get the aggregated popular models with optional filtering.

    Args:
        versions: Optional list of autosubmit versions to filter by
        limit: Optional maximum number of results

    Returns:
        AggregatedPopularModelsResponse: Response containing last extraction timestamp and list of aggregated popular models
    """
    app = request.app

    cache_key = "models:aggregated"

    request_id = get_current_request_id()

    try:
        cached_result = None
        if hasattr(app.state, "cache"):
            cached_result = app.state.cache.get(cache_key)
        if cached_result:
            ContextualLogger.info(
                f"Cache hit for aggregated popular models",
                extra={
                    "request_id": request_id,
                    "cache_key": cache_key,
                    "cache_hit": True,
                },
            )
            response = cached_result

            if limit is not None and hasattr(response, "models"):
                response = copy(response)
                response.models = response.models[:limit]

            return response

        ContextualLogger.info(
            f"Cache miss for aggregated popular models",
            extra={
                "request_id": request_id,
                "cache_key": cache_key,
                "cache_hit": False,
            },
        )

        transaction = TrPopularModelsAggregated()

        result = await transaction.execute()

        if limit is not None:
            result = result[:limit]

        response = AggregatedPopularModelsResponse.initialize(result)

        if hasattr(app.state, "cache"):
            request.app.state.cache.set(cache_key, response)

        ContextualLogger.info(
            "Retrieved aggregated popular models successfully",
            extra={
                "request_id": request_id,
                "cache_updated": True,
                "cache_key": cache_key,
            },
        )

        return response

    except Exception as e:

        if isinstance(e, ConnectionError) or "timeout" in str(e).lower():
            raise ServiceUnavailableException(
                "Service temporarily unavailable",
                context={"original_error": str(e), "cache_key": cache_key},
            )

        raise