"""
Endpoints operativos: health check y métricas básicas

Son los endpoints que usan los orquestadores (Kubernetes, Docker Swarm,
load balancers) y los equipos de operaciones para monitorear el servicio
"""

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_memory_store, get_stats_service
from app.schemas.stats import HealthResponse, StatsResponse
from app.services.memory_store import MemoryStore
from app.services.stats_service import StatsService

router = APIRouter(tags=["ops"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Verifica que el servicio esté operativo",
)
async def health_check() -> HealthResponse:
    """
    Health check mínimo (no chequea el LLM). 
    Si el proceso responde, el servicio está vivo
    """
    return HealthResponse()


@router.get(
    "/stats",
    response_model=StatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Métricas operativas en memoria",
)
async def get_stats(
    memory_store: MemoryStore = Depends(get_memory_store),
    stats_service: StatsService = Depends(get_stats_service),
) -> StatsResponse:
    """
    Devuelve los contadores acumulados desde que arrancó el proceso

    Las métricas se reinician cuando el servicio reinicia, igual que la
    memoria conversacional
    """
    snapshot = stats_service.snapshot(
        active_sessions=memory_store.active_session_count(),
    )
    return StatsResponse(**snapshot)