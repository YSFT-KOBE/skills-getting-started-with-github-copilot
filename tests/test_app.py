from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details():
    response = client.get("/activities")

    assert response.status_code == 200
    body = response.json()
    assert body.keys() == activities.keys()
    assert body["Chess Club"]["description"] == (
        "Learn strategies and compete in chess tournaments"
    )
    assert body["Chess Club"]["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
    assert body["Chess Club"]["max_participants"] == 12
    assert "michael@mergington.edu" in body["Chess Club"]["participants"]


def test_signup_adds_a_participant():
    email = "new.student@mergington.edu"

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for Chess Club"
    }
    assert email in activities["Chess Club"]["participants"]


def test_signup_returns_not_found_for_unknown_activity():
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_participant():
    email = "michael@mergington.edu"

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }


def test_remove_participant_removes_existing_participant():
    email = "michael@mergington.edu"

    response = client.delete(
        "/activities/Chess Club/participants",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Removed {email} from Chess Club"
    }
    assert email not in activities["Chess Club"]["participants"]


def test_remove_participant_returns_not_found_for_unknown_activity():
    response = client.delete(
        "/activities/Unknown Club/participants",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_remove_participant_returns_not_found_for_unknown_participant():
    response = client.delete(
        "/activities/Chess Club/participants",
        params={"email": "not-registered@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found"}