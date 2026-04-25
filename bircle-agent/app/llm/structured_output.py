"""
Parser con fallback para la salida JSON del LLM

El modelo puede devolver JSON malformado, con campos faltantes, o con valores
fuera de los dominios cerrados. Este módulo se encarga de:
1. Intentar parsear y validar la respuesta
2. Si falla, devolver una respuesta válida de fallback en lugar de crashear

"""
import json
import logging

from pydantic import ValidationError

from app.schemas.classification import ClassificationOutput
from app.schemas.message import MessageResponse

logger = logging.getLogger(__name__)


# Clasificación neutra que se usa cuando no podemos parsear la salida del LLM.
# Marca escalación a humano porque si el modelo falló, lo más seguro es que
# alguien revise el caso
_FALLBACK_CLASSIFICATION = ClassificationOutput(
    category="general",
    priority="low",
    intent="other",
    sentiment="neutral",
    requires_human_escalation=True,
    reasoning="No se pudo determinar la clasificación a partir de la salida del modelo.",
    confidence_score=0.0,
)

# Mensaje de fallback cuando ni siquiera podemos extraer un reply del LLM
_FALLBACK_REPLY = (
    "Disculpe, tuve un problema procesando tu mensaje. "
    "Un agente humano va a revisar la conversación en breve."
)


def _extract_json_text(raw_text: str) -> str:
    """Elimina bloques de markdown (```json ... ```) que Anthropic suele agregar"""
    text = raw_text.strip()
    if text.startswith("```"):
        # Saltar la primera línea (``` o ```json) y la última (```)
        lines = text.splitlines()
        text = "\n".join(lines[1:-1]).strip()
    return text


def parse_llm_response(raw_text: str) -> MessageResponse:
    """
    Parsea la respuesta cruda del LLM y la valida contra MessageResponse

    Si el JSON es inválido, le faltan campos, o algún valor está fuera de los
    dominios permitidos, devuelve un MessageResponse de fallback en lugar de
    propagar la excepción
    """
    # Paso 1: parsear el JSON
    try:
        data = json.loads(_extract_json_text(raw_text))
    except json.JSONDecodeError as exc:
        # Capturamos el output crudo para debbug
        logger.warning("LLM devolvió JSON inválido: %s | raw=%r", exc, raw_text[:500])
        return _build_fallback_response()

    # Paso 2: validar la estructura completa con Pydantic
    try:
        return MessageResponse(**data)
    
    except (ValidationError, TypeError) as exc:
        logger.warning("Salida del LLM no cumple el schema: %s | data=%r", exc, data)
        # Si el campo que falló es un Literal, loguear el valor recibido para
        # que sea fácil agregar un alias nuevo en classification.py
        if isinstance(exc, ValidationError):
            for error in exc.errors():
                if error.get("type") == "literal_error":
                    logger.warning(
                        "Valor fuera de dominio en campo '%s': recibido=%r — "
                        "considera agregar un alias en _INTENT_ALIASES o _CATEGORY_ALIASES",
                        " -> ".join(str(loc) for loc in error["loc"]),
                        error.get("input"),
                    )
        
        # Si el reply está presente y es texto, lo conservamos para no perder
        # la respuesta conversacional que el usuario va a ver
        partial_reply = data.get("reply") if isinstance(data, dict) else None
        
        return _build_fallback_response(reply_override=partial_reply)


def _build_fallback_response(reply_override: str | None = None) -> MessageResponse:
    """Construye una respuesta de fallback válida según el schema"""
    reply = reply_override if isinstance(reply_override, str) and reply_override.strip() else _FALLBACK_REPLY
    
    return MessageResponse(reply=reply, classification=_FALLBACK_CLASSIFICATION)