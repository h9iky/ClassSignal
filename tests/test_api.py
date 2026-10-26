def test_health_check(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_list_subjects(client):
    created = client.post(
        "/api/v1/subjects", json={"name": "Mathematics", "description": "Algebra and geometry"}
    )

    assert created.status_code == 201
    assert created.json()["name"] == "Mathematics"
    assert client.get("/api/v1/subjects").json() == [created.json()]


def test_duplicate_subject_returns_conflict(client):
    client.post("/api/v1/subjects", json={"name": "Mathematics"})

    response = client.post("/api/v1/subjects", json={"name": "Mathematics"})

    assert response.status_code == 409


def test_create_quarter_and_reject_invalid_values(client):
    valid = client.post("/api/v1/quarters", json={"school_year": "2025-2026", "number": 4})
    invalid_number = client.post("/api/v1/quarters", json={"school_year": "2025-2026", "number": 5})
    invalid_dates = client.post(
        "/api/v1/quarters",
        json={"school_year": "2025-2026", "number": 3, "starts_at": "2026-03-01", "ends_at": "2026-02-01"},
    )

    assert valid.status_code == 201
    assert invalid_number.status_code == 422
    assert invalid_dates.status_code == 422


def test_duplicate_quarter_returns_conflict(client):
    payload = {"school_year": "2025-2026", "number": 1}
    client.post("/api/v1/quarters", json=payload)

    response = client.post("/api/v1/quarters", json=payload)

    assert response.status_code == 409


def test_create_get_filter_and_patch_topic(client, base_records):
    subject, quarter = base_records
    payload = {
        "subject_id": subject["id"],
        "quarter_id": quarter["id"],
        "title": "Linear equations",
        "description": "Introduction",
    }
    created = client.post("/api/v1/topics", json=payload)

    assert created.status_code == 201
    topic_id = created.json()["id"]
    assert client.get(f"/api/v1/topics/{topic_id}").json()["title"] == "Linear equations"
    assert len(client.get(f"/api/v1/topics?subject_id={subject['id']}").json()) == 1
    assert len(client.get(f"/api/v1/topics?quarter_id={quarter['id']}").json()) == 1
    assert client.get("/api/v1/topics?subject_id=999").json() == []

    updated = client.patch(f"/api/v1/topics/{topic_id}", json={"title": "Equations", "status": "published"})

    assert updated.status_code == 200
    assert updated.json()["title"] == "Equations"
    assert updated.json()["status"] == "published"


def test_topic_rejects_missing_references_and_invalid_patch(client, base_records):
    subject, quarter = base_records
    response = client.post(
        "/api/v1/topics",
        json={"subject_id": subject["id"], "quarter_id": 999, "title": "Not saved"},
    )
    assert response.status_code == 404

    topic = client.post(
        "/api/v1/topics",
        json={"subject_id": subject["id"], "quarter_id": quarter["id"], "title": "Valid topic"},
    ).json()
    empty_patch = client.patch(f"/api/v1/topics/{topic['id']}", json={})
    invalid_status = client.patch(f"/api/v1/topics/{topic['id']}", json={"status": "visible"})

    assert empty_patch.status_code == 422
    assert invalid_status.status_code == 422


def test_unknown_topic_returns_not_found(client):
    response = client.get("/api/v1/topics/404")

    assert response.status_code == 404
