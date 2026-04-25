"""
Configuración central de la aplicación

Todas las variables sensibles y parámetros configurables se leen desde el
entorno (archivo .env en desarrollo, variables del sistema en producción)

"""

from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ruta absoluta al .env, funciona sin importar desde qué directorio se corra el servidor
_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """Settings de la aplicación, cargados desde variables de entorno."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Configuración del proveedor LLM ---

    # Proveedor a usar (provider.py)
    # "ollama" corre localmente y no requiere api key
    llm_provider: Literal["openai", "anthropic", "ollama"] = "ollama"

    llm_model_name: str = "llama3.2:3b"

    # API key del proveedor.
    # Es opcional a nivel schema porque Ollama (local) no la necesita,
    # pero se valida condicionalmente más abajo para los proveedores cloud.
    llm_api_key: str | None = Field(
        default=None,
        description="API key del proveedor LLM. Obligatoria para openai/anthropic, ignorada para ollama.",
    )

    # URL base del servidor de Ollama (solo aplica si llm_provider == "ollama")
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Endpoint del runtime de Ollama corriendo localmente o en red interna.",
    )

    # Valor default razonable para tareas de clasificación
    llm_temperature: float = Field(default=0.2, ge=0.0, le=2.0)

    # Timeout máximo para una llamada al LLM
    llm_timeout_seconds: int = Field(default=30, gt=0)

    # Cantidad máxima de mensajes que se conservan por sesión (para conservación de tokens)
    max_session_history: int = Field(default=20, gt=0)

    # Solo informativo, útil para logs
    app_environment: Literal["development", "staging", "production"] = "development"

    @model_validator(mode="after")
    def _validate_provider_credentials(self) -> "Settings":
        """
        Valida que los proveedores cloud tengan api key.

        Se hace acá (y no como `min_length=1` en el campo) porque la obligatoriedad
        depende del proveedor elegido. Fail-fast: si la combinación es inválida,
        Settings() falla en boot y la app no levanta.
        """
        cloud_providers = {"openai", "anthropic"}

        if self.llm_provider in cloud_providers:
            if not self.llm_api_key or not self.llm_api_key.strip():
                raise ValueError(
                    f"LLM_API_KEY es obligatoria cuando LLM_PROVIDER='{self.llm_provider}'."
                )

        return self


settings = Settings()
