"""
Factory que devuelve el cliente LLM configurado
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.core.config import settings


def get_llm() -> BaseChatModel:
    """
    Devuelve una instancia de ChatModel según el proveedor configurado.
    """

    if settings.llm_provider == "openai":
        return ChatOpenAI(
            model=settings.llm_model_name,
            api_key=settings.llm_api_key,
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout_seconds,

            # response_format fuerza al modelo a devolver JSON válido
            model_kwargs={"response_format": {"type": "json_object"}},
        )

    if settings.llm_provider == "anthropic":
        return ChatAnthropic(
            model=settings.llm_model_name,
            api_key=settings.llm_api_key,
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout_seconds,
        )

    if settings.llm_provider == "ollama":
        # Ollama corre local, no usa api key.
        # No se pasa format="json" aquí: with_structured_output() lo inyecta
        # automáticamente con el JSON Schema completo del modelo Pydantic
        return ChatOllama(
            model=settings.llm_model_name,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature,
        )

    # Si el proveedor no es reconocido, se lanza un error
    raise ValueError(f"Proveedor LLM no soportado: {settings.llm_provider}")
