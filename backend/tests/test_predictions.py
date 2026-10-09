def test_create_prediction_returns_valid_result(client, auth_headers, sample_customer_payload):
    response = client.post("/api/predictions", json=sample_customer_payload, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["customer_id"] == "CUST-TEST-001"
    assert 0.0 <= body["churn_probability"] <= 1.0
    assert body["prediction"] in (0, 1)
    assert body["risk_level"] in ("Low", "Medium", "High")
    assert body["model_used"] == "RandomForestClassifier"


def test_prediction_persists_customer_and_history(client, auth_headers, sample_customer_payload):
    client.post("/api/predictions", json=sample_customer_payload, headers=auth_headers)

    customer_resp = client.get("/api/customers/CUST-TEST-001", headers=auth_headers)
    assert customer_resp.status_code == 200

    history_resp = client.get("/api/predictions/customer/CUST-TEST-001", headers=auth_headers)
    assert history_resp.status_code == 200
    assert len(history_resp.json()) == 1


def test_prediction_invalid_input(client, auth_headers, sample_customer_payload):
    bad_payload = dict(sample_customer_payload)
    bad_payload["monthly_charges"] = -50  # violates ge=0 constraint
    response = client.post("/api/predictions", json=bad_payload, headers=auth_headers)
    assert response.status_code == 422


def test_prediction_requires_auth(client, sample_customer_payload):
    response = client.post("/api/predictions", json=sample_customer_payload)
    assert response.status_code == 401


def test_list_predictions_with_filters(client, auth_headers, sample_customer_payload):
    client.post("/api/predictions", json=sample_customer_payload, headers=auth_headers)

    response = client.get("/api/predictions", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = client.get("/api/predictions?customer_id=CUST-TEST-001", headers=auth_headers)
    assert response.json()["total"] == 1

    response = client.get("/api/predictions?customer_id=NO-SUCH-ID", headers=auth_headers)
    assert response.json()["total"] == 0


def test_high_risk_endpoint_returns_list(client, auth_headers, sample_customer_payload):
    client.post("/api/predictions", json=sample_customer_payload, headers=auth_headers)
    response = client.get("/api/predictions/high-risk", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
