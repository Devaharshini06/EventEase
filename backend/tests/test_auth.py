def test_registration_success(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "Clara Oswald",
            "role": "attendee",
            "organization": "Gallifrey Labs",
        },
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert "token" in data
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["primary_role"] == "attendee"


def test_duplicate_email_registration(client):
    payload = {
        "email": "dup@example.com",
        "password": "SecurePassword123!",
        "full_name": "First User",
        "role": "attendee",
    }
    resp1 = client.post("/api/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/auth/register", json=payload)
    assert resp2.status_code == 409
    assert "already exists" in resp2.get_json()["error"].lower()


def test_public_registration_forbids_admin_role(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "hacker@example.com",
            "password": "SecurePassword123!",
            "full_name": "Malicious Actor",
            "role": "admin",
        },
    )
    assert resp.status_code == 403


def test_valid_and_invalid_login(client):
    client.post(
        "/api/auth/register",
        json={
            "email": "loginuser@example.com",
            "password": "ValidPassword123!",
            "full_name": "Login Tester",
            "role": "organizer",
        },
    )

    bad_resp = client.post(
        "/api/auth/login",
        json={"email": "loginuser@example.com", "password": "WrongPassword!"},
    )
    assert bad_resp.status_code == 401

    good_resp = client.post(
        "/api/auth/login",
        json={"email": "loginuser@example.com", "password": "ValidPassword123!"},
    )
    assert good_resp.status_code == 200
    assert "token" in good_resp.get_json()


def test_missing_or_invalid_token_rejected(client):
    no_token_resp = client.get("/api/auth/me")
    assert no_token_resp.status_code == 401

    bad_token_resp = client.get(
        "/api/auth/me",
        headers={"Authentication-Token": "invalid-forged-token-value"},
    )
    assert bad_token_resp.status_code == 401


def test_logout_invalidates_token(client, auth_tokens):
    headers = auth_tokens["att1"]["headers"]
    me_before = client.get("/api/auth/me", headers=headers)
    assert me_before.status_code == 200

    logout_resp = client.post("/api/auth/logout", headers=headers)
    assert logout_resp.status_code == 200

    me_after = client.get("/api/auth/me", headers=headers)
    assert me_after.status_code == 401


def test_role_restrictions_on_protected_endpoints(client, auth_tokens):
    # Attendee cannot access organizer dashboard or admin endpoints
    att_headers = auth_tokens["att1"]["headers"]
    assert client.get("/api/dashboard/organizer", headers=att_headers).status_code == 403
    assert client.get("/api/dashboard/admin", headers=att_headers).status_code == 403
    assert client.get("/api/users", headers=att_headers).status_code == 403

    # Organizer can access organizer dashboard, but not admin endpoints
    org_headers = auth_tokens["org1"]["headers"]
    assert client.get("/api/dashboard/organizer", headers=org_headers).status_code == 200
    assert client.get("/api/dashboard/admin", headers=org_headers).status_code == 403
    assert client.get("/api/users", headers=org_headers).status_code == 403
