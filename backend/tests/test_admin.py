def test_admin_user_management_and_role_changes(client, auth_tokens):
    admin_headers = auth_tokens["admin"]["headers"]
    att1_id = auth_tokens["att1"]["user"]["id"]

    # List users
    users_resp = client.get("/api/users", headers=admin_headers)
    assert users_resp.status_code == 200
    assert users_resp.get_json()["total"] >= 5

    # Promote attendee 1 to organizer
    role_resp = client.put(
        f"/api/users/{att1_id}/role",
        headers=admin_headers,
        json={"role": "organizer"},
    )
    assert role_resp.status_code == 200
    assert role_resp.get_json()["user"]["primary_role"] == "organizer"


def test_prevent_unauthorized_role_changes(client, auth_tokens):
    att1_id = auth_tokens["att1"]["user"]["id"]

    # Organizer cannot change user roles
    org_attempt = client.put(
        f"/api/users/{att1_id}/role",
        headers=auth_tokens["org1"]["headers"],
        json={"role": "admin"},
    )
    assert org_attempt.status_code == 403

    # Attendee cannot change their own role
    att_attempt = client.put(
        f"/api/users/{att1_id}/role",
        headers=auth_tokens["att1"]["headers"],
        json={"role": "admin"},
    )
    assert att_attempt.status_code == 403


def test_deactivated_user_blocked_from_protected_operations(client, auth_tokens):
    admin_headers = auth_tokens["admin"]["headers"]
    att2_id = auth_tokens["att2"]["user"]["id"]
    att2_headers = auth_tokens["att2"]["headers"]

    # Deactivate att2
    deact_resp = client.put(
        f"/api/users/{att2_id}/status",
        headers=admin_headers,
        json={"active": False},
    )
    assert deact_resp.status_code == 200
    assert deact_resp.get_json()["user"]["active"] is False

    # Existing token is immediately invalidated (uniquifier rotated -> 401/403)
    me_resp = client.get("/api/auth/me", headers=att2_headers)
    assert me_resp.status_code in (401, 403)

    # Deactivated user cannot log in
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "att2@test.io", "password": "Password123!"},
    )
    assert login_resp.status_code == 403


def test_admin_category_crud(client, auth_tokens):
    admin_headers = auth_tokens["admin"]["headers"]
    org_headers = auth_tokens["org1"]["headers"]

    # Organizer cannot create category
    assert (
        client.post(
            "/api/categories",
            headers=org_headers,
            json={"name": "Unauthorized Category"},
        ).status_code
        == 403
    )

    # Admin creates category
    create_resp = client.post(
        "/api/categories",
        headers=admin_headers,
        json={"name": "Robotics & Hardware", "description": "Embedded systems and robotics."},
    )
    assert create_resp.status_code == 201
    cat_id = create_resp.get_json()["category"]["id"]

    # Duplicate category name rejected with 409
    dup_resp = client.post(
        "/api/categories",
        headers=admin_headers,
        json={"name": "Robotics & Hardware"},
    )
    assert dup_resp.status_code == 409

    # Admin updates category
    upd_resp = client.put(
        f"/api/categories/{cat_id}",
        headers=admin_headers,
        json={"description": "Updated description"},
    )
    assert upd_resp.status_code == 200

    # Admin deletes unused category
    del_resp = client.delete(f"/api/categories/{cat_id}", headers=admin_headers)
    assert del_resp.status_code == 200
