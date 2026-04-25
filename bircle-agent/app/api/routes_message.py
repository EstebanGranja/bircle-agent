"""
Endpoint principal del agente conversacional
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_agent_service
from app.schemas.message import MessageRequest, MessageResponse
from app.services.agent_service import AgentService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["message"])


# Endpoint para procesar un mensaje del usuario y devolver la respuesta del agente
@router.post(
    "/message",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Procesa un turno conversacional",
)
async def handle_message(
    request: MessageRequest,
    agent_service: AgentService = Depends(get_agent_service),
) -> MessageResponse:
    """
    Procesa un mensaje del usuario
    """
    try:
        return await agent_service.process_turn(
            session_id=request.session_id,
            user_message=request.message,
        )
    
    except TimeoutError:
        # El LLM tardó demasiado en responder
        logger.warning("Timeout del LLM en sesión %s", request.session_id)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="El modelo tardó demasiado en responder. Intentá de nuevo",
        )
    
    except Exception as exc:
        # Cualquier otro error (red, auth, proveedor caído)
        # Lo logueamos completo pero no lo exponemos al cliente
        logger.exception("Error procesando mensaje en sesión %s: %s", request.session_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno procesando el mensaje.",
        )