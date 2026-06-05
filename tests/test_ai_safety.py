from app.models.schemas import AiInsightRequest
from app.services.ai_insights import build_ai_prompt, normalize_ai_insight
from app.services.rate_limit import is_ai_rate_limited, reset_rate_limit_state
from app.services.redaction import redact_sensitive_text


def test_redacts_sensitive_text():
    text = (
        "Contact test@example.com with api_key=abc123 "
        "and Authorization Bearer sk_test_secret. "
        "Account 1234567890123456."
    )

    redacted = redact_sensitive_text(text)

    assert "test@example.com" not in redacted
    assert "abc123" not in redacted
    assert "sk_test_secret" not in redacted
    assert "1234567890123456" not in redacted
    assert "[REDACTED_EMAIL]" in redacted


def test_ai_prompt_uses_redacted_diagnostic_data():
    prompt = build_ai_prompt(
        AiInsightRequest(
            target="google.com",
            ping_data="Contact admin@example.com and password=hunter2",
            traceroute_data="Bearer secret-token",
            ports={
                "443": "Open",
            },
        )
    )

    assert "admin@example.com" not in prompt
    assert "hunter2" not in prompt
    assert "secret-token" not in prompt
    assert "[REDACTED_EMAIL]" in prompt


def test_normalize_ai_insight_defaults_invalid_response_fields():
    insight = normalize_ai_insight(
        {
            "summary": "Reviewed.",
            "risk_level": "critical",
            "probable_causes": "not-list",
            "recommended_next_steps": "not-list",
        }
    )

    assert insight["risk_level"] == "medium"
    assert insight["probable_causes"] == []
    assert insight["recommended_next_steps"] == []


def test_ai_rate_limit_helper_blocks_after_limit():
    reset_rate_limit_state()

    assert is_ai_rate_limited(
        "test-client",
        now=1000,
        max_requests=2,
        window_seconds=60,
    ) is False

    assert is_ai_rate_limited(
        "test-client",
        now=1001,
        max_requests=2,
        window_seconds=60,
    ) is False

    assert is_ai_rate_limited(
        "test-client",
        now=1002,
        max_requests=2,
        window_seconds=60,
    ) is True