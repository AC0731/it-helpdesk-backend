def test_ai_insight_returns_local_fallback_without_api_key(client):
    response = client.post(
        "/api/ai/insight",
        json={
            "target": "google.com",
            "ping_data": "Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)",
            "traceroute_data": "Traceroute command timed out after 20 seconds",
            "ports": {
                "80": "Open",
                "443": "Open",
                "22": "Closed",
            },
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["target"] == "google.com"
    assert body["insight"]["provider"] in {"local_rules", "local_rules_fallback"}
    assert body["insight"]["summary"]
    assert body["insight"]["risk_level"] in {"low", "medium", "high"}
    assert len(body["insight"]["probable_causes"]) > 0
    assert len(body["insight"]["recommended_next_steps"]) > 0


def test_ai_insight_validates_target(client):
    response = client.post(
        "/api/ai/insight",
        json={
            "target": "",
            "ping_data": "",
            "traceroute_data": "",
            "ports": {},
        },
    )

    assert response.status_code == 422