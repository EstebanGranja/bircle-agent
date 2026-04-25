"""
Eventos de ciclo de vida de la aplicación FastAPI

El lifespan corre código una sola vez al arrancar el servidor (startup) y
una sola vez al apagarlo (shutdown). Sirve para inicializar servicios
compartidos como la memoria conversacional y el contador de stats

"""

from contextlib import asynccontextmanager
from time import monotonic

from fastapi import FastAPI

from app.core.config import settings
from app.services.memory_store import MemoryStore
from app.services.stats_service import StatsService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Inicializa los servicios compartidos antes de aceptar requests y los
    deja disponibles en app.state para que los routers puedan accederlos
    """
    # --- Startup ---
    app.state.memory_store = MemoryStore(max_history=settings.max_session_history)
    app.state.stats_service = StatsService()
    app.state.started_at = monotonic()

    # Todo lo de arriba corre antes de aceptar requests; 
    # todo lo de abajo corre cuando el servidor se apaga

    yield

    # --- Shutdown ---
    # No hay recursos externos que cerrar (DB o conexiones persistentes) 
    # Si en el futuro se agregan, se cierran acá