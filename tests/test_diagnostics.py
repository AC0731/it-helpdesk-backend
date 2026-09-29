import app.api.diagnostics as diagnostics_api
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


def test_diagnostics_creates_history_entry(client, monkeypatch):
    async def fake_execute(_target):
        return {
            "target": "8.8.8.8",
            "resolved_ip": "8.8.8.8",
            "results": {
                "ping": "Ping OK",
                "traceroute": "Traceroute OK",
                "ports": {"80": "Open", "443": "Open"},
            },
        }

    monkeypatch.setattr(
        diagnostics_api,
        "execute_bounded_diagnostic",
        fake_execute,
    )

    response = client.post(
        "/api/diagnostics",
        json={"target": "8.8.8.8"},
        headers={"X-Request-ID": "CASE-42"},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["request_id"] == "CASE-42"
    assert response.headers["x-request-id"] == "CASE-42"
    assert body["diagnostic_id"] == 1
    assert body["target"] == "8.8.8.8"
    assert body["resolved_ip"] == "8.8.8.8"
    assert body["results"]["ping"] == "Ping OK"
    assert body["results"]["traceroute"] == "Traceroute OK"
    assert body["results"]["ports"]["443"] == "Open"

    history_response = client.get("/api/diagnostics/history")

    assert history_response.status_code == 200

    history = history_response.json()

    assert history["count"] == 1
    assert history["diagnostics"][0]["target"] == "8.8.8.8"


def test_diagnostics_returns_timeout_state(client, monkeypatch):
    async def timeout(_target):
        raise diagnostics_api.DiagnosticTimeoutError("deadline exceeded")

    monkeypatch.setattr(
        diagnostics_api,
        "execute_bounded_diagnostic",
        timeout,
    )

    response = client.post(
        "/api/diagnostics",
        json={"target": "8.8.8.8"},
        headers={"X-Request-ID": "TIMEOUT-7"},
    )

    assert response.status_code == 504
    assert response.json()["detail"] == (
        "Diagnostic execution timed out before completion."
    )
    assert response.headers["x-request-id"] == "TIMEOUT-7"


def test_diagnostics_returns_capacity_state(client, monkeypatch):
    async def saturated(_target):
        raise diagnostics_api.DiagnosticCapacityError("full")

    monkeypatch.setattr(
        diagnostics_api,
        "execute_bounded_diagnostic",
        saturated,
    )

    response = client.post(
        "/api/diagnostics",
        json={"target": "8.8.8.8"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Diagnostic capacity is currently full. Retry shortly."
    )


def test_persistence_failure_does_not_create_history(client, monkeypatch):
    async def fake_execute(_target):
        return {
            "target": "8.8.8.8",
            "resolved_ip": "8.8.8.8",
            "results": {
                "ping": "Ping OK",
                "traceroute": "Traceroute OK",
                "ports": {"443": "Open"},
            },
        }

    monkeypatch.setattr(
        diagnostics_api,
        "execute_bounded_diagnostic",
        fake_execute,
    )

    original_commit = Session.commit

    def fail_commit(self):
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(Session, "commit", fail_commit)

    response = client.post(
        "/api/diagnostics",
        json={"target": "8.8.8.8"},
        headers={"X-Request-ID": "DB-FAIL-1"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Diagnostics completed but could not be saved."
    )
    assert response.headers["x-request-id"] == "DB-FAIL-1"

    monkeypatch.setattr(Session, "commit", original_commit)

    history_response = client.get("/api/diagnostics/history")
    assert history_response.status_code == 200
    assert history_response.json()["count"] == 0


def test_diagnostics_rejects_localhost(client):
    response = client.post("/api/diagnostics", json={"target": "localhost"})
    assert response.status_code == 400


def test_diagnostics_rejects_private_ip(client):
    response = client.post("/api/diagnostics", json={"target": "192.168.1.1"})
    assert response.status_code == 400


def test_diagnostics_rejects_ipv6_loopback(client):
    response = client.post("/api/diagnostics", json={"target": "::1"})
    assert response.status_code == 400


def test_diagnostics_rejects_full_url(client):
    response = client.post(
        "/api/diagnostics",
        json={"target": "https://google.com"},
    )
    assert response.status_code == 400
