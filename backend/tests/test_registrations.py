from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from flask_security.utils import hash_password
from backend.app.models import db, User, Role, Event, Category


def _create_event(client, org_headers, status="PUBLISHED", capacity=10, days_ahead=10, deadline_days=8):
    cat_id = client.get("/api/categories").get_json()["categories"][0]["id"]
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    resp = client.post(
        "/api/events",
        headers=org_headers,
        json={
            "title": "Test Registration Event",
            "description": "Event created to verify registration workflows and constraints.",
            "category_id": cat_id,
            "venue": "Main Auditorium",
            "city": "Boston",
            "start_datetime": (now + timedelta(days=days_ahead)).isoformat(),
            "end_datetime": (now + timedelta(days=days_ahead, hours=4)).isoformat(),
            "registration_deadline": (now + timedelta(days=deadline_days)).isoformat(),
            "capacity": capacity,
            "price": 0.0,
            "status": status,
        },
    )
    return resp.get_json()["event"]


def test_successful_and_duplicate_registration(client, auth_tokens):
    ev = _create_event(client, auth_tokens["org1"]["headers"], capacity=5)
    att_headers = auth_tokens["att1"]["headers"]

    # First registration succeeds
    reg1 = client.post(f"/api/events/{ev['id']}/registrations", headers=att_headers)
    assert reg1.status_code == 201
    reg_data = reg1.get_json()["registration"]
    assert reg_data["registration_reference"].startswith("EVT-")
    assert reg_data["status"] == "CONFIRMED"

    # Duplicate registration rejected with 409
    reg2 = client.post(f"/api/events/{ev['id']}/registrations", headers=att_headers)
    assert reg2.status_code == 409


def test_registration_rejected_for_draft_or_past_deadline(app, client, auth_tokens):
    org_headers = auth_tokens["org1"]["headers"]
    att_headers = auth_tokens["att1"]["headers"]

    # Draft event rejected
    draft_ev = _create_event(client, org_headers, status="DRAFT")
    resp_draft = client.post(f"/api/events/{draft_ev['id']}/registrations", headers=att_headers)
    assert resp_draft.status_code == 400

    # Past deadline event rejected
    expired_ev = _create_event(client, org_headers, status="PUBLISHED")
    with app.app_context():
        ev_obj = db.session.get(Event, expired_ev["id"])
        ev_obj.registration_deadline = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2)
        db.session.commit()

    resp_expired = client.post(f"/api/events/{expired_ev['id']}/registrations", headers=att_headers)
    assert resp_expired.status_code == 400
    assert "deadline" in resp_expired.get_json()["error"].lower()


def test_capacity_enforcement_and_cancellation_consistency(client, auth_tokens):
    ev = _create_event(client, auth_tokens["org1"]["headers"], capacity=1)
    att1_headers = auth_tokens["att1"]["headers"]
    att2_headers = auth_tokens["att2"]["headers"]

    # Attendee 1 takes the only seat
    r1 = client.post(f"/api/events/{ev['id']}/registrations", headers=att1_headers)
    assert r1.status_code == 201
    reg_id = r1.get_json()["registration"]["id"]

    # Verify event remaining_capacity is 0
    ev_after = client.get(f"/api/events/{ev['id']}").get_json()["event"]
    assert ev_after["registered_count"] == 1
    assert ev_after["remaining_capacity"] == 0

    # Attendee 2 is rejected because capacity is full
    r2 = client.post(f"/api/events/{ev['id']}/registrations", headers=att2_headers)
    assert r2.status_code == 409

    # Attendee 1 cancels registration -> capacity is restored to 1
    cancel_resp = client.post(f"/api/registrations/{reg_id}/cancel", headers=att1_headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.get_json()["registration"]["status"] == "CANCELLED"

    ev_restored = client.get(f"/api/events/{ev['id']}").get_json()["event"]
    assert ev_restored["registered_count"] == 0
    assert ev_restored["remaining_capacity"] == 1

    # Now Attendee 2 can register for the freed seat
    r2_retry = client.post(f"/api/events/{ev['id']}/registrations", headers=att2_headers)
    assert r2_retry.status_code == 201


def test_unauthorized_access_to_other_attendees_registration(client, auth_tokens):
    ev = _create_event(client, auth_tokens["org1"]["headers"], capacity=5)
    r1 = client.post(
        f"/api/events/{ev['id']}/registrations",
        headers=auth_tokens["att1"]["headers"],
    ).get_json()["registration"]

    # Attendee 2 cannot view or cancel Attendee 1's registration
    view_resp = client.get(
        f"/api/registrations/{r1['id']}",
        headers=auth_tokens["att2"]["headers"],
    )
    assert view_resp.status_code == 403

    cancel_resp = client.post(
        f"/api/registrations/{r1['id']}/cancel",
        headers=auth_tokens["att2"]["headers"],
    )
    assert cancel_resp.status_code == 403


def test_concurrent_registration_for_last_available_place(app, client, auth_tokens):
    """
    Spawns 5 concurrent registration requests against a real file-backed SQLite database
    for an event with capacity=1, verifying atomic capacity enforcement prevents overselling.
    """
    ev = _create_event(client, auth_tokens["org1"]["headers"], capacity=1)
    event_id = ev["id"]

    tokens = []
    with app.app_context():
        datastore = app.extensions["security"].datastore
        att_role = Role.query.filter_by(name="attendee").first()
        for i in range(5):
            u = datastore.create_user(
                email=f"concurrent_{i}@test.io",
                password=hash_password("Password123!"),
                full_name=f"Concurrent User {i}",
                active=True,
            )
            datastore.add_role_to_user(u, att_role)
            db.session.flush()
            tokens.append(u.get_auth_token())
        db.session.commit()

    def attempt_register(tok):
        with app.test_client() as local_client:
            res = local_client.post(
                f"/api/events/{event_id}/registrations",
                headers={"Authentication-Token": tok},
            )
            return res.status_code

    with ThreadPoolExecutor(max_workers=5) as pool:
        statuses = list(pool.map(attempt_register, tokens))

    assert statuses.count(201) == 1
    assert statuses.count(409) == 4

    with app.app_context():
        final_event = db.session.get(Event, event_id)
        assert final_event.registered_count == 1
        assert final_event.remaining_capacity == 0
