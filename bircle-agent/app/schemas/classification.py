"""
Clasificación de mensajes de usuario en categorías, prioridades, 
intenciones y sentimientos

"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

CategoryType = Literal["billing", "support", "sales", "complaint", "general"]
PriorityType = Literal["low", "medium", "high", "urgent"]
IntentType = Literal["ask_info", "complain", "request_action", "report_issue", "other"]
SentimentType = Literal["positive", "neutral", "negative"]

# Estas tablas de aliases permiten que el modelo use sinónimos para los valores esperados
_INTENT_ALIASES: dict[str, str] = {
    "request_info": "ask_info",
    "get_info": "ask_info",
    "information_request": "ask_info",
    "info_request": "ask_info",
    "complaint": "complain",
    "complaining": "complain",
    "make_complaint": "complain",
    "action_request": "request_action",
    "issue_report": "report_issue",
    "bug_report": "report_issue",
}

_CATEGORY_ALIASES: dict[str, str] = {
    "complaints": "complaint",
    "technical_support": "support",
    "technical": "support",
    "commerce": "sales",
    "purchase": "sales",
}


class ClassificationOutput(BaseModel):
    """Clasificación del turno actual del usuario"""

    category: CategoryType
    priority: PriorityType
    intent: IntentType
    sentiment: SentimentType
    requires_human_escalation: bool
    reasoning: str = Field(
        min_length=10,
        description="Breve explicación de por qué se asignó esta clasificación",
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confianza del modelo en la clasificación, entre 0.0 y 1.0",
    )

    @field_validator("intent", mode="before")
    @classmethod
    def normalize_intent(cls, v: object) -> object:
        if isinstance(v, str):
            return _INTENT_ALIASES.get(v.lower().strip(), v)
        return v

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, v: object) -> object:
        if isinstance(v, str):
            return _CATEGORY_ALIASES.get(v.lower().strip(), v)
        return v
