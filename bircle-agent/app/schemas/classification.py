"""
Structured classification of a single conversation turn
"""

from typing import Literal

from pydantic import BaseModel, Field

CategoryType = Literal["billing", "support", "sales", "complaint", "general"]
PriorityType = Literal["low", "medium", "high", "urgent"]
IntentType = Literal["ask_info", "complain", "request_action", "report_issue", "other"]
SentimentType = Literal["positive", "neutral", "negative"]


class ClassificationOutput(BaseModel):
    """Classification of the current user turn."""

    category: CategoryType
    priority: PriorityType
    intent: IntentType
    sentiment: SentimentType
    requires_human_escalation: bool
    reasoning: str = Field(
        min_length=10,
        description="Brief explanation of why this classification was assigned.",
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Model confidence in the classification, between 0.0 and 1.0.",
    )