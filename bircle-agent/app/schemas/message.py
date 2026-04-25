"""
Request and response models for the conversational endpoint
"""

from pydantic import BaseModel, Field

from app.schemas.classification import ClassificationOutput


class MessageRequest(BaseModel):
    """Body for POST /message."""

    session_id: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Identifier of the conversation session. History is kept in memory under this key.",
    )
    message: str = Field(
        min_length=1,
        max_length=4000,
        description="Current user message to be processed by the agent.",
    )


class MessageResponse(BaseModel):
    """Response from POST /message — agent reply plus structured classification."""

    reply: str = Field(min_length=1)
    classification: ClassificationOutput