def create_ticket(client, target="8.8.8.8", priority="medium"):
    return client.post(
        "/api/ticket",
        json={
            "user_id": "Demo Agent",
            "target": target,
            "ping_data": "Ping OK",
            "traceroute_data": "Traceroute OK",
            "priority": priority,
        },
    )


def test_ticket_create_list_lookup_and_update(client):
    create_response = create_ticket(client)

    assert create_response.status_code == 200

    created = create_response.json()
    ticket_id = created["ticket_id"]

    assert created["status"] == "success"
    assert created["ticket"]["target"] == "8.8.8.8"
    assert created["ticket"]["status"] == "open"
    assert created["ticket"]["priority"] == "medium"

    list_response = client.get("/api/tickets")

    assert list_response.status_code == 200

    ticket_list = list_response.json()

    assert ticket_list["count"] == 1
    assert ticket_list["tickets"][0]["ticket_id"] == ticket_id

    lookup_response = client.get(f"/api/tickets/{ticket_id}")

    assert lookup_response.status_code == 200
    assert lookup_response.json()["ticket_id"] == ticket_id

    update_response = client.patch(
        f"/api/tickets/{ticket_id}",
        json={"status": "in_progress"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["ticket"]["status"] == "in_progress"

    resolved_response = client.patch(
        f"/api/tickets/{ticket_id}",
        json={"status": "resolved"},
    )

    assert resolved_response.status_code == 200
    assert resolved_response.json()["ticket"]["status"] == "resolved"


def test_ticket_rejects_private_target(client):
    response = create_ticket(client, target="127.0.0.1")

    assert response.status_code == 400


def test_ticket_rejects_invalid_priority(client):
    response = create_ticket(client, priority="critical")

    assert response.status_code == 400


def test_ticket_rejects_invalid_status_update(client):
    create_response = create_ticket(client)
    ticket_id = create_response.json()["ticket_id"]

    update_response = client.patch(
        f"/api/tickets/{ticket_id}",
        json={"status": "waiting"},
    )

    assert update_response.status_code == 400

def test_ticket_analytics_counts_queue_metrics(client):
    create_ticket(client, target="8.8.8.8", priority="medium")
    high_response = create_ticket(client, target="1.1.1.1", priority="high")
    urgent_response = create_ticket(client, target="google.com", priority="urgent")

    high_ticket_id = high_response.json()["ticket_id"]
    urgent_ticket_id = urgent_response.json()["ticket_id"]

    client.patch(
        f"/api/tickets/{high_ticket_id}",
        json={"status": "in_progress"},
    )

    client.patch(
        f"/api/tickets/{urgent_ticket_id}",
        json={"status": "resolved"},
    )

    response = client.get("/api/tickets/analytics")

    assert response.status_code == 200

    analytics = response.json()

    assert analytics["total"] == 3
    assert analytics["by_status"]["open"] == 1
    assert analytics["by_status"]["in_progress"] == 1
    assert analytics["by_status"]["resolved"] == 1
    assert analytics["by_status"]["closed"] == 0
    assert analytics["by_priority"]["medium"] == 1
    assert analytics["by_priority"]["high"] == 1
    assert analytics["by_priority"]["urgent"] == 1
    assert analytics["high_priority_total"] == 2

def test_ticket_list_filters_by_priority(client):
    create_ticket(client, target="8.8.8.8", priority="medium")
    create_ticket(client, target="1.1.1.1", priority="urgent")

    response = client.get("/api/tickets?priority=urgent")

    assert response.status_code == 200

    body = response.json()

    assert body["count"] == 1
    assert body["tickets"][0]["target"] == "1.1.1.1"
    assert body["tickets"][0]["priority"] == "urgent"


def test_ticket_list_filters_by_search(client):
    create_ticket(client, target="google.com", priority="medium")
    create_ticket(client, target="cloudflare.com", priority="medium")

    response = client.get("/api/tickets?search=cloudflare")

    assert response.status_code == 200

    body = response.json()

    assert body["count"] == 1
    assert body["tickets"][0]["target"] == "cloudflare.com"


def test_ticket_list_rejects_invalid_priority_filter(client):
    response = client.get("/api/tickets?priority=critical")

    assert response.status_code == 400
