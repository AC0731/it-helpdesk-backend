import re

SENSITIVE_PATTERNS = [
    (re.compile(r"(?i)(bearer\s+)[a-z0-9._\-]+"), r"\1[REDACTED_TOKEN]"),
    (re.compile(r"(?i)(api[_\- ]?key\s*[:=]\s*)[a-z0-9._\-]+"), r"\1[REDACTED_API_KEY]"),
    (re.compile(r"(?i)(secret\s*[:=]\s*)[a-z0-9._\-]+"), r"\1[REDACTED_SECRET]"),
    (re.compile(r"(?i)(password\s*[:=]\s*)[^\s]+"), r"\1[REDACTED_PASSWORD]"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[REDACTED_EMAIL]"),
    (re.compile(r"(https?://)[^:\s/]+:[^@\s/]+@"), r"\1[REDACTED_CREDENTIALS]@"),
    (re.compile(r"\b\d{12,}\b"), "[REDACTED_LONG_ID]"),
]


def redact_sensitive_text(value: object) -> str:
    text = "" if value is None else str(value)

    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)

    return text


def redact_ports(ports: dict[str, str]) -> dict[str, str]:
    return {
        redact_sensitive_text(port): redact_sensitive_text(status)
        for port, status in ports.items()
    }