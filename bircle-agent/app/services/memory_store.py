"""
Almacén en memoria del historial conversacional por sesión

Sin persistencia, el estado vive solo mientras corre el proceso
"""

import threading
from collections import defaultdict

from langchain_core.messages import BaseMessage


class MemoryStore:
    """
    Almacena el historial de mensajes por session_id de forma thread-safe

    Cada sesión es una lista de BaseMessage de LangChain. El historial 
    se trunca cuando supera max_history para evitar que el contexto crezca sin límite
    """

    def __init__(self, max_history: int) -> None:
        # defaultdict evita tener que chequear si la sesión existe antes de
        # agregarle mensajes: la primera vez que se accede, se crea vacía
        self._sessions: dict[str, list[BaseMessage]] = defaultdict(list)

        # Lock para proteger el dict y las listas de modificaciones concurrentes
        self._lock = threading.Lock()

        self._max_history = max_history

    def get_history(self, session_id: str) -> list[BaseMessage]:
        """Devuelve una copia del historial para evitar mutaciones externas"""
        with self._lock:
            # Crea una copia superficial. El caller puede iterar
            # tranquilo aunque otro thread modifique el original
            return list(self._sessions[session_id])

    def append_messages(self, session_id: str, messages: list[BaseMessage]) -> None:
        """Agrega mensajes al final del historial y trunca si excede el máximo"""
        with self._lock:
            self._sessions[session_id].extend(messages)

            # Si quedamos por encima del límite, recortamos del principio
            # y conservamos los más recientes
            if len(self._sessions[session_id]) > self._max_history:
                self._sessions[session_id] = self._sessions[session_id][-self._max_history:]

    def reset_session(self, session_id: str) -> bool:
        """
        Elimina el historial de una sesión

        Devuelve True si la sesión existía, False si no. Útil para que el
        endpoint de reset pueda responder 404 cuando corresponde
        """
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def active_session_count(self) -> int:
        """Cantidad de sesiones con al menos un mensaje en memoria"""
        with self._lock:
            return len(self._sessions)