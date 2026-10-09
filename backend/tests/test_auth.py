def test_login_success(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "Admin123!"})
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "wrong-password"})
    assert response.status_code == 401


def test_login_unknown_user(client):
    response = client.post("/api/auth/login", json={"username": "nobody", "password": "whatever"})
    assert response.status_code == 401


def test_protected_route_requires_token(client):
    response = client.get("/api/customers")
    assert response.status_code == 401


def test_protected_route_with_valid_token(client, auth_headers):
    response = client.get("/api/customers", headers=auth_headers)
    assert response.status_code == 200


def test_me_endpoint(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "admin"
