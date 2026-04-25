"""
Models for operational endpoints: /health and /stats
"""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class StatsResponse(BaseModel):
    """In-memory operational metrics maintained by the application."""

    total_requests: int
    total_errors: int
    active_sessions: int
    uptime_seconds: float