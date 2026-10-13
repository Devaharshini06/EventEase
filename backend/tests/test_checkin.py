from datetime import datetime, timedelta, timezone


def _setup_event_and_registration(client, auth_tokens):
    cat_id = client.get("/api/categories").get_json()["categories"][0]["id"]
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    ev = client.post(
        "/api/events",
        headers=auth_tokens["org1"]["headers"],
        json={
            "title": "Check-In Verification Workshop",
            "description": "Workshop for testing attendee check-in workflows.",
            "category_id": cat_id,
            "venue": "Studio 300",
            "city": "Seattle",
            "start_datetime": (now + timedelta(days=5)).isoformat(),
            "end_datetime": (now + timedelta(days=5, hours=3)).isoformat(),
            "registration_deadline": (now + timedelta(days=4)).isoformat(),
            "capacity": 20,
            "price": 0.0,
            "status": "PUBLISHED",
        },
    ).get_json()["event"]

    reg = client.post(
        f"/api/events/{ev['id']}/registrations",
        headers=auth_tokens["att1"]["headers"],
    ).get_json()["registration"]

    return ev, reg


def test_valid_and_duplicate_check_in(client, auth_tokens):
    ev, reg = _setup_event_and_registration(client, auth_tokens)
    org1_headers = auth_tokens["org1"]["headers"]

    # Valid check-in by reference
    checkin_resp = client.post(
        f"/api/events/{ev['id']}/check-in",
        headers=org1_headers,
        json={"registration_reference": reg["registration_reference"]},
    )
    assert checkin_resp.status_code == 200
    checked_data = checkin_resp.get_json()["registration"]
    assert checked_data["status"] == "CHECKED_IN"
    assert checked_data["checked_in_at"] is not None

    # Duplicate check-in rejected with 409
    dup_resp = client.post(
        f"/api/events/{ev['id']}/check-in",
        headers=org1_headers,
        json={"registration_reference": reg["registration_reference"]},
    )
    assert dup_resp.status_code == 409


def test_invalid_and_cancelled_registration_check_in_rejected(client, auth_tokens):
    ev, reg = _setup_event_and_registration(client, auth_tokens)
    org1_headers = auth_tokens["org1"]["headers"]

    # Invalid reference -> 404
    invalid_resp = client.post(
        f"/api/events/{ev['id']}/check-in",
        headers=org1_headers,
        json={"registration_reference": "EVT-XXXX-0000"},
    )
    assert invalid_resp.status_code == 404

    # Cancel the registration, then attempt check-in -> 400
    client.post(f"/api/registrations/{reg['id']}/cancel", headers=auth_tokens["att1"]["headers"])
    cancelled_checkin = client.post(
        f"/api/registrations/{reg['id']}/check-in",
        headers=org1_headers,
    )
    assert cancelled_checkin.status_code == 400


def test_unauthorized_check_in_attempts(client, auth_tokens):
    ev, reg = _setup_event_and_registration(client, auth_tokens)

    # Attendee cannot check themselves in
    att_attempt = client.post(
        f"/api/registrations/{reg['id']}/check-in",
        headers=auth_tokens["att1"]["headers"],
    )
    assert att_attempt.status_code == 403

    # Organizer 2 cannot check in attendees for Organizer 1's event
    org2_attempt = client.post(
        f"/api/registrations/{reg['id']}/check-in",
        headers=auth_tokens["org2"]["headers"],
    )
    assert org2_attempt.status_code == 403
