import os
import pytest
from fastapi.testclient import TestClient

os.environ["USE_MONGOMOCK"] = "true"

from app.main import app
from app.database import get_db, reset_db_client

@pytest.fixture(autouse=True)
def setup_test_db():
    reset_db_client()
    db = get_db()
    db.rooms.delete_many({})
    db.cabinets.delete_many({})
    db.items.delete_many({})
    yield
    db.rooms.delete_many({})
    db.cabinets.delete_many({})
    db.items.delete_many({})

client = TestClient(app)

def test_cabinet_crud_and_moving():
    # Setup 2 rooms
    r1 = client.post("/api/rooms", data={"name": "Living Room"}).json()
    r2 = client.post("/api/rooms", data={"name": "Study Room"}).json()

    # 1. Create cabinet in Living Room
    res = client.post("/api/cabinets", data={"name": "TV Stand", "room_id": r1["id"]})
    assert res.status_code == 201
    cab = res.json()
    assert cab["name"] == "TV Stand"
    assert cab["room_id"] == r1["id"]
    cab_id = cab["id"]

    # 2. List cabinets
    res = client.get("/api/cabinets")
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 3. Get cabinet detail
    res = client.get(f"/api/cabinets/{cab_id}")
    assert res.status_code == 200
    detail = res.json()
    assert detail["room"]["id"] == r1["id"]
    assert detail["items"] == []

    # 4. Move cabinet to Study Room
    res = client.put(f"/api/cabinets/{cab_id}", json={"room_id": r2["id"], "name": "Desk Cabinet"})
    assert res.status_code == 200
    updated = res.json()
    assert updated["room_id"] == r2["id"]
    assert updated["name"] == "Desk Cabinet"

    # Verify detail shows updated room
    detail = client.get(f"/api/cabinets/{cab_id}").json()
    assert detail["room"]["id"] == r2["id"]

    # 5. Upload cabinet image
    res = client.post(
        f"/api/cabinets/{cab_id}/image",
        files={"image": ("cab.jpg", b"cabinet picture", "image/jpeg")}
    )
    assert res.status_code == 200
    assert res.json()["image_url"].startswith("/uploads/cabinets/")

    # 6. Delete cabinet
    res = client.delete(f"/api/cabinets/{cab_id}")
    assert res.status_code == 200
    assert client.get(f"/api/cabinets/{cab_id}").status_code == 404
