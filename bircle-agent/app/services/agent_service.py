"""
Orquestador del turno conversacional

Es el punto donde se unen memoria, prompt, LLM y parser. El router llama a
process_turn() y recibe un MessageResponse listo para devolver al cliente
"""

import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import Runnable

from app.llm.prompts import SALES_AGENT_SYSTEM_PROMPT
from app.llm.structured_output import parse_llm_response
from app.schemas.message import MessageResponse
from app.services.memory_store import MemoryStore
from app.services.stats_service import StatsService

logger = logging.getLogger(__name__)


class AgentService:
    """
    Procesa un turno: arma el contexto, llama al LLM, parsea, persiste

    Recibe sus dependencias por constructor (facilita testing y separación de responsabilidades)
    """

    def __init__(
        self,
        llm: BaseChatModel,
        memory_store: MemoryStore,
        stats_service: StatsService,
    ) -> None:
        self._llm = llm
        self._memory_store = memory_store
        self._stats_service = stats_service

        # with_structured_output pasa el JSON Schema de MessageResponse a Ollama
        self._structured_llm: Runnable = llm.with_structured_output(MessageResponse)

    async def process_turn(self, session_id: str, user_message: str) -> MessageResponse:
        """
        Procesa un mensaje del usuario y devuelve la respuesta del agente
        """

        self._stats_service.record_request()

        history = self._memory_store.get_history(session_id)
        messages = [
            SystemMessage(content=SALES_AGENT_SYSTEM_PROMPT),
            *history,
            HumanMessage(content=user_message),
        ]

        result = await self._invoke_structured(messages)

        self._memory_store.append_messages(
            session_id=session_id,
            messages=[
                HumanMessage(content=user_message),
                AIMessage(content=result.reply),
            ],
        )

        return result

    async def _invoke_structured(self, messages: list) -> MessageResponse:
        """
        Intenta obtener una respuesta estructurada del LLM.

        Flujo principal: with_structured_output → Pydantic válido garantizado.
        Fallback: llamada cruda al LLM + parse_llm_response con respuesta degradada.
        """
        try:
            result = await self._structured_llm.ainvoke(messages)
            # with_structured_output devuelve el objeto Pydantic directamente
            if isinstance(result, MessageResponse):
                return result
            # Algunos proveedores devuelven el dict en lugar del modelo instanciado
            return MessageResponse.model_validate(result)

        except Exception as exc:
            logger.warning(
                "with_structured_output falló, activando fallback manual: %s", exc
            )
            self._stats_service.record_error()

        # Fallback: llamada cruda para recuperar al menos el texto de respuesta
        try:
            raw_response = await self._llm.ainvoke(messages)
            return parse_llm_response(raw_text=raw_response.content)
        except Exception as exc:
            logger.error("El fallback también falló: %s", exc)
            self._stats_service.record_error()
            raise
