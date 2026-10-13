from datetime import datetime, timedelta, timezone


def _valid_event_payload(category_id=1, status="PUBLISHED", capacity=50):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return {
        "title": "Cloud Native Architecture Deep Dive",
        "description": "Comprehensive engineering session on Kubernetes networking and service mesh telemetry.",
        "category_id": category_id,
        "venue": "Grand Tech Center Hall A",
        "city": "San Francisco",
        "start_datetime": (now + timedelta(days=10)).isoformat(),
        "end_datetime": (now + timedelta(days=10, hours=6)).isoformat(),
        "registration_deadline": (now + timedelta(days=8)).isoformat(),
        "capacity": capacity,
        "price": 25.0,
        "status": status,
    }


def test_create_read_update_event(client, auth_tokens):
    org_headers = auth_tokens["org1"]["headers"]
    cats = client.get("/api/categories").get_json()["categories"]
    cat_id = cats[0]["id"]

    # Create
    create_resp = client.post(
        "/api/events",
        headers=org_headers,
        json=_valid_event_payload(category_id=cat_id, status="PUBLISHED", capacity=40),
    )
    assert create_resp.status_code == 201
    event_id = create_resp.get_json()["event"]["id"]

    # Read
    get_resp = client.get(f"/api/events/{event_id}")
    assert get_resp.status_code == 200
    assert get_resp.get_json()["event"]["title"] == "Cloud Native Architecture Deep Dive"

    # Update
    update_resp = client.put(
        f"/api/events/{event_id}",
        headers=org_headers,
        json={"title": "Updated Cloud Architecture Summit", "capacity": 60},
    )
    assert update_resp.status_code == 200
    assert update_resp.get_json()["event"]["title"] == "Updated Cloud Architecture Summit"
    assert update_resp.get_json()["event"]["capacity"] == 60


def test_delete_draft_and_cancel_published_event(client, auth_tokens):
    org_headers = auth_tokens["org1"]["headers"]
    cat_id = client.get("/api/categories").get_json()["categories"][0]["id"]

    # Draft event -> permanently deleted
    draft_resp = client.post(
        "/api/events",
        headers=org_headers,
        json=_valid_event_payload(category_id=cat_id, status="DRAFT"),
    )
    draft_id = draft_resp.get_json()["event"]["id"]
    del_draft = client.delete(f"/api/events/{draft_id}", headers=org_headers)
    assert del_draft.status_code == 200
    assert del_draft.get_json()["action"] == "DELETED"
    assert client.get(f"/api/events/{draft_id}", headers=org_headers).status_code == 404

    # Published event -> transitioned to CANCELLED to preserve history
    pub_resp = client.post(
        "/api/events",
        headers=org_headers,
        json=_valid_event_payload(category_id=cat_id, status="PUBLISHED"),
    )
    pub_id = pub_resp.get_json()["event"]["id"]
    del_pub = client.delete(f"/api/events/{pub_id}", headers=org_headers)
    assert del_pub.status_code == 200
    assert del_pub.get_json()["action"] == "CANCELLED"
    assert del_pub.get_json()["event"]["status"] == "CANCELLED"


def test_invalid_date_ranges_and_capacity(client, auth_tokens):
    org_headers = auth_tokens["org1"]["headers"]
    cat_id = client.get("/api/categories").get_json()["categories"][0]["id"]
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # End before start
    bad_dates = _valid_event_payload(category_id=cat_id)
    bad_dates["start_datetime"] = (now + timedelta(days=10)).isoformat()
    bad_dates["end_datetime"] = (now + timedelta(days=9)).isoformat()
    resp1 = client.post("/api/events", headers=org_headers, json=bad_dates)
    assert resp1.status_code == 400

    # Registration deadline after start
    bad_deadline = _valid_event_payload(category_id=cat_id)
    bad_deadline["registration_deadline"] = (now + timedelta(days=11)).isoformat()
    resp2 = client.post("/api/events", headers=org_headers, json=bad_deadline)
    assert resp2.status_code == 400

    # Invalid capacity (0 or negative)
    bad_cap = _valid_event_payload(category_id=cat_id, capacity=0)
    resp3 = client.post("/api/events", headers=org_headers, json=bad_cap)
    assert resp3.status_code == 400


def test_missing_event_and_unauthorized_modification(client, auth_tokens):
    org1_headers = auth_tokens["org1"]["headers"]
    org2_headers = auth_tokens["org2"]["headers"]
    att_headers = auth_tokens["att1"]["headers"]
    cat_id = client.get("/api/categories").get_json()["categories"][0]["id"]

    # Missing event
    assert client.get("/api/events/99999").status_code == 404
    assert client.put("/api/events/99999", headers=org1_headers, json={"title": "Nope"}).status_code == 404

    # Attendee cannot create event
    att_create = client.post(
        "/api/events",
        headers=att_headers,
        json=_valid_event_payload(category_id=cat_id),
    )
    assert att_create.status_code == 403

    # Organizer 2 cannot modify Organizer 1's event
    ev = client.post(
        "/api/events",
        headers=org1_headers,
        json=_valid_event_payload(category_id=cat_id),
    ).get_json()["event"]

    org2_update = client.put(
        f"/api/events/{ev['id']}",
        headers=org2_headers,
        json={"title": "Hijacked Title"},
    )
    assert org2_update.status_code == 403
