def test_dashboard_stats_empty_state(client, auth_headers):
    response = client.get("/api/dashboard/stats", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_customers"] == 0
    assert body["total_predictions"] == 0
    assert body["overall_churn_rate"] == 0.0


def test_dashboard_stats_after_prediction(client, auth_headers, sample_customer_payload):
    client.post("/api/predictions", json=sample_customer_payload, headers=auth_headers)
    response = client.get("/api/dashboard/stats", headers=auth_headers)
    body = response.json()
    assert body["total_customers"] == 1
    assert body["total_predictions"] == 1
    assert body["high_risk_customers"] + body["medium_risk_customers"] + body["low_risk_customers"] == 1


def test_churn_distribution(client, auth_headers, sample_customer_payload):
    client.post("/api/predictions", json=sample_customer_payload, headers=auth_headers)
    response = client.get("/api/dashboard/churn-distribution", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["churned"] + body["not_churned"] == 1


def test_segmentation_endpoint(client, auth_headers, sample_customer_payload):
    client.post("/api/customers", json=sample_customer_payload, headers=auth_headers)
    response = client.get("/api/dashboard/segmentation", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["by_contract"]["Month-to-month"] == 1
