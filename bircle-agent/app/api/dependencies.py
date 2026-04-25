"""
Dependencias compartidas para los routers
"""

from fastapi import Request

from app.llm.provider import get_llm
from app.services.agent_service import AgentService
from app.services.memory_store import MemoryStore
from app.services.stats_service import StatsService


def get_memory_store(request: Request) -> MemoryStore:
    """Devuelve la instancia única de MemoryStore creada en el lifespan"""
    return request.app.state.memory_store


def get_stats_service(request: Request) -> StatsService:
    """Devuelve la instancia única de StatsService creada en el lifespan"""
    return request.app.state.stats_service


def get_agent_service(request: Request) -> AgentService:
    """
    Construye un AgentService por request, inyectándole sus dependencias
    """
    return AgentService(
        llm=get_llm(),
        memory_store=request.app.state.memory_store,
        stats_service=request.app.state.stats_service,
    )