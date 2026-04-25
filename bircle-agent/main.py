"""
Punto de entrada de la aplicación FastAPI

Construye la app, registra los routers y configura el manejo global de
errores

"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes_message import router as message_router
from app.api.routes_ops import router as ops_router
from app.api.routes_session import router as session_router
from app.core.config import settings
from app.core.lifespan import lifespan
from app.schemas.errors import ErrorResponse

# Configuración básica de logging para que aparezcan los logs de la app
# en stdout (compatible con Docker)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Factory que construye y configura la aplicación FastAPI
    """

    app = FastAPI(
        title="Bircle Sales Agent API",
        description=(
            "Agente conversacional de ventas con clasificación estructurada "
            "turn-by-turn. Mantiene historial en memoria por sesión"
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # Registro de routers
    app.include_router(message_router)
    app.include_router(session_router)
    app.include_router(ops_router)

    # Handlers globales de excepciones para que toda respuesta de error
    # tenga el mismo formato (ErrorResponse)
    _register_exception_handlers(app)

    logger.info(
        "Aplicación inicializada | provider=%s | model=%s | environment=%s",
        settings.llm_provider,
        settings.llm_model_name,
        settings.app_environment,
    )

    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """Registra los handlers globales de errores con formato consistente"""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """
        Captura errores de validación de Pydantic (request body inválido)

        Unificamos el formato que usa FastAPI por defecto con ErrorResponse 
        para que el cliente siempre reciba la misma forma
        """
        # exc.errors() trae el detalle estructurado de qué campo falló
        # Lo serializamos como string para que entre en el campo `detail`
        first_error = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(loc) for loc in first_error.get("loc", []))
        message = first_error.get("msg", "Datos de entrada inválidos.")

        error_response = ErrorResponse(
            error="validation_error",
            detail=f"{field}: {message}" if field else message,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=error_response.model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """
        Red de seguridad final: captura cualquier excepción no manejada

        Si llegamos acá es que algo se nos escapó en los routers. Logueamos
        el traceback completo y devolvemos un 500 limpio al cliente, sin
        exponer detalles internos
        """
        logger.exception("Excepción no manejada en %s %s", request.method, request.url.path)
        error_response = ErrorResponse(
            error="internal_error",
            detail="Error interno del servidor.",
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )


app = create_app()