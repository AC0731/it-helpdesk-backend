import json

import httpx

from app.core.config import get_settings
from app.models.schemas import AiInsightRequest
from app.services.redaction import redact_ports, redact_sensitive_text


def build_local_insight(payload: AiInsightRequest) -> dict:
    open_ports = [
        port
        for port, status in payload.ports.items()
        if str(status).lower() == "open"
    ]

    risk_level = "low"

    if "3389" in open_ports or "22" in open_ports:
        risk_level = "medium"

    if "No response" in payload.ping_data or "100% loss" in payload.ping_data:
        risk_level = "high"

    probable_causes = [
        "The target may be reachable if common web ports are open.",
        "Route diagnostics may be limited by server environment restrictions.",
    ]

    if not open_ports:
        probable_causes.append("No common ports were detected as open during the scan.")

    if "timed out" in payload.traceroute_data.lower():
        probable_causes.append("Traceroute may be blocked or unavailable on the hosting environment.")

    next_steps = [
        "Confirm the target value is correct.",
        "Review ping output for packet loss or latency spikes.",
        "Review open ports and confirm whether they match the expected service.",
        "Escalate if the issue affects a production service or repeats across multiple users.",
    ]

    return {
        "provider": "local_rules",
        "summary": f"Diagnostics were reviewed for {payload.target}.",
        "risk_level": risk_level,
        "probable_causes": probable_causes,
        "recommended_next_steps": next_steps,
    }


def build_ai_prompt(payload: AiInsightRequest) -> str:
    safe_target = redact_sensitive_text(payload.target)
    safe_ping = redact_sensitive_text(payload.ping_data)
    safe_traceroute = redact_sensitive_text(payload.traceroute_data)
    safe_ports = redact_ports(payload.ports)

    return f"""
Analyze this IT support diagnostic result and return practical troubleshooting guidance.

Target:
{safe_target}

Ping output:
{safe_ping}

Traceroute output:
{safe_traceroute}

Port scan:
{safe_ports}

Return JSON only with this shape:
{{
  "summary": "short plain-English summary",
  "risk_level": "low | medium | high",
  "probable_causes": ["cause 1", "cause 2"],
  "recommended_next_steps": ["step 1", "step 2", "step 3"]
}}
""".strip()


def extract_response_text(response_body: dict) -> str:
    if isinstance(response_body.get("output_text"), str):
        return response_body["output_text"]

    output_items = response_body.get("output", [])

    for item in output_items:
        for content in item.get("content", []):
            text = content.get("text")

            if isinstance(text, str):
                return text

    return ""


def normalize_ai_insight(parsed: dict) -> dict:
    risk_level = parsed.get("risk_level", "medium")

    if risk_level not in {"low", "medium", "high"}:
        risk_level = "medium"

    probable_causes = parsed.get("probable_causes", [])
    recommended_next_steps = parsed.get("recommended_next_steps", [])

    if not isinstance(probable_causes, list):
        probable_causes = []

    if not isinstance(recommended_next_steps, list):
        recommended_next_steps = []

    return {
        "provider": "openai",
        "summary": str(parsed.get("summary", "")),
        "risk_level": risk_level,
        "probable_causes": probable_causes,
        "recommended_next_steps": recommended_next_steps,
    }


async def build_ai_insight(payload: AiInsightRequest) -> dict:
    settings = get_settings()

    if not settings.openai_api_key:
        return build_local_insight(payload)

    request_body = {
        "model": settings.ai_model,
        "instructions": (
            "You are an IT support troubleshooting assistant. "
            "Use cautious, practical, non-destructive advice. "
            "Do not invent facts that are not present in the diagnostic data. "
            "Never request passwords, secrets, or private credentials."
        ),
        "input": build_ai_prompt(payload),
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json=request_body,
            )

        response.raise_for_status()

        response_text = extract_response_text(response.json())
        parsed = json.loads(response_text)

        return normalize_ai_insight(parsed)
    except Exception:
        fallback = build_local_insight(payload)
        fallback["provider"] = "local_rules_fallback"
        return fallback