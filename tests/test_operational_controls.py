from app.services.rate_limit import (
    is_ai_rate_limited,
    rate_limit_state_size,
    reset_rate_limit_state,
)


def test_request_id_is_preserved_and_security_headers_are_added(client):
    response = client.get("/", headers={"X-Request-ID": "INC-2026-0042"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "INC-2026-0042"
    assert float(response.headers["x-process-time-ms"]) >= 0
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_invalid_request_id_is_replaced(client):
    response = client.get("/", headers={"X-Request-ID": "invalid request id"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] != "invalid request id"
    assert len(response.headers["x-request-id"]) == 32


def test_readiness_checks_database(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}


def test_rate_limit_prunes_stale_clients():
    reset_rate_limit_state()

    assert is_ai_rate_limited(
        "stale-client",
        now=100,
        max_requests=2,
        window_seconds=10,
    ) is False
    assert rate_limit_state_size() == 1

    assert is_ai_rate_limited(
        "current-client",
        now=200,
        max_requests=2,
        window_seconds=10,
    ) is False

    assert rate_limit_state_size() == 1


def test_rate_limit_bounds_unique_client_state():
    reset_rate_limit_state()

    for index in range(4):
        assert is_ai_rate_limited(
            f"client-{index}",
            now=100 + index,
            max_requests=2,
            window_seconds=60,
            max_clients=3,
        ) is False

    assert rate_limit_state_size() == 3
