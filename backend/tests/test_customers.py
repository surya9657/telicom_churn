def test_create_customer_success(client, auth_headers, sample_customer_payload):
    response = client.post("/api/customers", json=sample_customer_payload, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["customer_id"] == "CUST-TEST-001"


def test_create_duplicate_customer_fails(client, auth_headers, sample_customer_payload):
    client.post("/api/customers", json=sample_customer_payload, headers=auth_headers)
    response = client.post("/api/customers", json=sample_customer_payload, headers=auth_headers)
    assert response.status_code == 409


def test_create_customer_invalid_data(client, auth_headers, sample_customer_payload):
    bad_payload = dict(sample_customer_payload)
    bad_payload["gender"] = "Unknown"  # not a valid enum value
    response = client.post("/api/customers", json=bad_payload, headers=auth_headers)
    assert response.status_code == 422


def test_create_customer_missing_field(client, auth_headers, sample_customer_payload):
    bad_payload = dict(sample_customer_payload)
    del bad_payload["monthly_charges"]
    response = client.post("/api/customers", json=bad_payload, headers=auth_headers)
    assert response.status_code == 422


def test_get_customer_by_id(client, auth_headers, sample_customer_payload):
    client.post("/api/customers", json=sample_customer_payload, headers=auth_headers)
    response = client.get("/api/customers/CUST-TEST-001", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["customer_id"] == "CUST-TEST-001"


def test_get_nonexistent_customer(client, auth_headers):
    response = client.get("/api/customers/DOES-NOT-EXIST", headers=auth_headers)
    assert response.status_code == 404


def test_list_customers_returns_created_customer(client, auth_headers, sample_customer_payload):
    client.post("/api/customers", json=sample_customer_payload, headers=auth_headers)
    response = client.get("/api/customers", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["customer_id"] == "CUST-TEST-001"


def test_delete_customer(client, auth_headers, sample_customer_payload):
    client.post("/api/customers", json=sample_customer_payload, headers=auth_headers)
    response = client.delete("/api/customers/CUST-TEST-001", headers=auth_headers)
    assert response.status_code == 204

    response = client.get("/api/customers/CUST-TEST-001", headers=auth_headers)
    assert response.status_code == 404
