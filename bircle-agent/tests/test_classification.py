"""Tests del schema ClassificationOutput y sus aliases"""

import pytest
from pydantic import ValidationError

from app.schemas.classification import ClassificationOutput


def _valid_payload(**overrides) -> dict:
    """Devuelve un payload válido base, con overrides opcionales"""
    payload = {
        "category": "sales",
        "priority": "medium",
        "intent": "ask_info",
        "sentiment": "neutral",
        "requires_human_escalation": False,
        "reasoning": "El usuario consulta información comercial.",
        "confidence_score": 0.8,
    }
    payload.update(overrides)
    return payload


def test_valid_payload_builds_classification():
    """Un payload válido construye el modelo sin errores"""
    cls = ClassificationOutput(**_valid_payload())
    assert cls.category == "sales"
    assert cls.confidence_score == 0.8


@pytest.mark.parametrize(
    "raw_intent, normalized",
    [
        ("request_info", "ask_info"),
        ("get_info", "ask_info"),
        ("information_request", "ask_info"),
        ("info_request", "ask_info"),
        ("complaint", "complain"),
        ("complaining", "complain"),
        ("make_complaint", "complain"),
        ("action_request", "request_action"),
        ("issue_report", "report_issue"),
        ("bug_report", "report_issue"),
    ],
)
def test_intent_aliases_are_normalized(raw_intent, normalized):
    """Los alias de intent se mapean al valor canónico"""
    cls = ClassificationOutput(**_valid_payload(intent=raw_intent))
    assert cls.intent == normalized


@pytest.mark.parametrize(
    "raw_category, normalized",
    [
        ("complaints", "complaint"),
        ("technical_support", "support"),
        ("technical", "support"),
        ("commerce", "sales"),
        ("purchase", "sales"),
    ],
)
def test_category_aliases_are_normalized(raw_category, normalized):
    """Los alias de category se mapean al valor canónico"""
    cls = ClassificationOutput(**_valid_payload(category=raw_category))
    assert cls.category == normalized


def test_intent_alias_is_case_insensitive():
    """El alias de intent normaliza ignorando mayúsculas y espacios"""
    cls = ClassificationOutput(**_valid_payload(intent="  REQUEST_INFO  "))
    assert cls.intent == "ask_info"


def test_invalid_category_raises():
    """Una categoría fuera del dominio cerrado y sin alias falla"""
    with pytest.raises(ValidationError):
        ClassificationOutput(**_valid_payload(category="random_value"))


def test_invalid_priority_raises():
    """Una prioridad fuera del dominio cerrado falla"""
    with pytest.raises(ValidationError):
        ClassificationOutput(**_valid_payload(priority="critical"))


def test_invalid_sentiment_raises():
    """Un sentiment fuera del dominio cerrado falla"""
    with pytest.raises(ValidationError):
        ClassificationOutput(**_valid_payload(sentiment="angry"))


def test_reasoning_below_min_length_raises():
    """reasoning con menos de 10 caracteres falla"""
    with pytest.raises(ValidationError):
        ClassificationOutput(**_valid_payload(reasoning="corto"))


@pytest.mark.parametrize("score", [-0.1, 1.1, 2.0])
def test_confidence_score_out_of_bounds_raises(score):
    """confidence_score fuera de [0.0, 1.0] falla"""
    with pytest.raises(ValidationError):
        ClassificationOutput(**_valid_payload(confidence_score=score))


@pytest.mark.parametrize("score", [0.0, 0.5, 1.0])
def test_confidence_score_in_bounds_accepted(score):
    """confidence_score dentro de [0.0, 1.0] es válido"""
    cls = ClassificationOutput(**_valid_payload(confidence_score=score))
    assert cls.confidence_score == score


def test_missing_required_field_raises():
    """Falta un campo obligatorio → falla"""
    payload = _valid_payload()
    del payload["category"]
    with pytest.raises(ValidationError):
        ClassificationOutput(**payload)
