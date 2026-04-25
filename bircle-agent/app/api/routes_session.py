"""
Endpoint de gestión de sesión: permite limpiar el historial de una sesión

Es parte del bonus que pide la consigna ("Mecanismo simple para limpiar o
resetear una sesión en memoria"). Útil cuando un usuario quiere arrancar
una conversación nueva sin esperar a que se reinicie el servicio
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_memory_store
from app.services.memory_store import MemoryStore

router = APIRouter(tags=["session"])


@router.delete(
    "/session/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Resetea el historial de una sesión",
)
async def reset_session(
    session_id: str,
    memory_store: MemoryStore = Depends(get_memory_store),
) -> None:
    """
    Elimina todo el historial asociado a session_id

    Devuelve 204 si la sesión existía, 404 si no había nada que borrar
    """
    existed = memory_store.reset_session(session_id)

    if not existed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe una sesión activa con id '{session_id}'.",
        )

    # 204 No Content: el reset fue exitoso pero no hay body que devolver
    return None