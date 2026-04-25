"""
Configuración central de la aplicación

Todas las variables sensibles y parámetros configurables se leen desde el
entorno (archivo .env en desarrollo, variables del sistema en producción)

"""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings de la aplicación, cargados desde variables de entorno."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Configuración del proveedor LLM ---

    # Proveedor a usar (provider.py)
    llm_provider: Literal["openai", "anthropic"] = "openai"

    llm_model_name: str = "gpt-4o-mini"

    # API key del proveedor (obligatoria)
    llm_api_key: str = Field(
        min_length=1,
        description="API key del proveedor LLM configurado.",
    )

    # Valor default razonable para tareas de clasificación
    llm_temperature: float = Field(default=0.2, ge=0.0, le=2.0)

    # Timeout máximo para una llamada al LLM
    llm_timeout_seconds: int = Field(default=30, gt=0)

    # Cantidad máxima de mensajes que se conservan por sesión (para conservación de tokens)
    max_session_history: int = Field(default=20, gt=0)

    # Solo informativo, útil para logs
    app_environment: Literal["development", "staging", "production"] = "development"


settings = Settings()