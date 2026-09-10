def test_health_and_api_documentation_are_available(client):
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json() == {
        "code": 0,
        "message": "success",
        "data": {"status": "ok"},
    }

    assert client.get("/doc.html").status_code == 200
    schema_response = client.get("/openapi.json")
    assert schema_response.status_code == 200
    paths = schema_response.json()["paths"]
    assert "/api/orders" in paths
    assert "/api/orders/{id}/pickup" in paths
    assert "/api/orders/verify" in paths
