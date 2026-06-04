import app.api.diagnostics as diagnostics_api


def test_diagnostics_creates_history_entry(client, monkeypatch):
    monkeypatch.setattr(diagnostics_api, "run_ping", lambda target: "Ping OK")
    monkeypatch.setattr(diagnostics_api, "run_traceroute", lambda target: "Traceroute OK")
    monkeypatch.setattr(
        diagnostics_api,
        "run_port_scan",
        lambda target: {"80": "Open", "443": "Open"},
    )

    response = client.post("/api/diagnostics", json={"target": "8.8.8.8"})

    assert response.status_code == 200

    body = response.json()

    assert body["diagnostic_id"] == 1
    assert body["target"] == "8.8.8.8"
    assert body["results"]["ping"] == "Ping OK"
    assert body["results"]["traceroute"] == "Traceroute OK"
    assert body["results"]["ports"]["443"] == "Open"

    history_response = client.get("/api/diagnostics/history")

    assert history_response.status_code == 200

    history = history_response.json()

    assert history["count"] == 1
    assert history["diagnostics"][0]["target"] == "8.8.8.8"


def test_diagnostics_rejects_localhost(client):
    response = client.post("/api/diagnostics", json={"target": "localhost"})

    assert response.status_code == 400


def test_diagnostics_rejects_private_ip(client):
    response = client.post("/api/diagnostics", json={"target": "192.168.1.1"})

    assert response.status_code == 400


def test_diagnostics_rejects_full_url(client):
    response = client.post("/api/diagnostics", json={"target": "https://google.com"})

    assert response.status_code == 400
