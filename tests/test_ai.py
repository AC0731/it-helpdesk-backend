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


def test_ai_insight_can_be_saved(client):
    response = client.post(
        "/api/ai/insight/save",
        json={
            "target": "google.com",
            "ping_data": "Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)",
            "traceroute_data": "Traceroute command timed out after 20 seconds",
            "ports": {
                "80": "Open",
                "443": "Open",
            },
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
    assert body["insight"]["id"] > 0
    assert body["insight"]["target"] == "google.com"
    assert body["insight"]["summary"]
    assert len(body["insight"]["recommended_next_steps"]) > 0


def test_saved_ai_insights_can_be_listed(client):
    client.post(
        "/api/ai/insight/save",
        json={
            "target": "google.com",
            "ping_data": "Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)",
            "traceroute_data": "Traceroute command timed out after 20 seconds",
            "ports": {
                "80": "Open",
            },
        },
    )

    response = client.get("/api/ai/insights")

    assert response.status_code == 200

    body = response.json()

    assert body["count"] == 1
    assert body["insights"][0]["target"] == "google.com"


def test_saved_ai_insight_rejects_missing_ticket(client):
    response = client.post(
        "/api/ai/insight/save",
        json={
            "ticket_id": "TKT-DOES-NOT-EXIST",
            "target": "google.com",
            "ping_data": "Ping OK",
            "traceroute_data": "Trace OK",
            "ports": {},
        },
    )

    assert response.status_code == 404

def test_saved_ai_insight_can_be_deleted(client):
    create_response = client.post(
        "/api/ai/insight/save",
        json={
            "target": "google.com",
            "ping_data": "Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)",
            "traceroute_data": "Traceroute command timed out after 20 seconds",
            "ports": {
                "80": "Open",
            },
        },
    )

    insight_id = create_response.json()["insight"]["id"]

    delete_response = client.delete(f"/api/ai/insights/{insight_id}")

    assert delete_response.status_code == 200
    assert delete_response.json()["deleted_id"] == insight_id

    list_response = client.get("/api/ai/insights")

    assert list_response.status_code == 200
    assert list_response.json()["count"] == 0


def test_delete_saved_ai_insight_returns_404_for_missing_record(client):
    response = client.delete("/api/ai/insights/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Saved insight not found."


def test_saving_same_ai_insight_twice_returns_existing_record(client):
    payload = {
        "target": "google.com",
        "ping_data": "Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)",
        "traceroute_data": "Traceroute command timed out after 20 seconds",
        "ports": {
            "80": "Open",
            "443": "Open",
        },
    }

    first_response = client.post("/api/ai/insight/save", json=payload)
    second_response = client.post("/api/ai/insight/save", json=payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["status"] == "success"
    assert second_response.json()["status"] == "already_saved"
    assert first_response.json()["insight"]["id"] == second_response.json()["insight"]["id"]

    list_response = client.get("/api/ai/insights")

    assert list_response.status_code == 200
    assert list_response.json()["count"] == 1
