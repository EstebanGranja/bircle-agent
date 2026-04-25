"""
Contadores operativos del proceso

Métricas básicas que se exponen en /stats
"""

import threading
from time import monotonic


class StatsService:
    """
    Mantiene contadores thread-safe de la operación de la API
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._total_requests = 0
        self._total_errors = 0
        self._started_at = monotonic()

    def record_request(self) -> None:
        """Suma un request al contador. Se llama al inicio de cada turno"""
        with self._lock:
            self._total_requests += 1

    def record_error(self) -> None:
        """Suma un error al contador. Se llama cuando un turno falla"""
        with self._lock:
            self._total_errors += 1

    def snapshot(self, active_sessions: int) -> dict:
        """
        Devuelve una foto consistente de las métricas.

        active_sessions se recibe como parámetro porque vive en el MemoryStore
        """
        with self._lock:
            return {
                "total_requests": self._total_requests,
                "total_errors": self._total_errors,
                "active_sessions": active_sessions,
                "uptime_seconds": monotonic() - self._started_at,
            }