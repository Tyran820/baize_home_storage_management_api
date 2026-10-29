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

def test_room_crud_and_image():
    # 1. Create room without image
    res = client.post("/api/rooms", data={"name": "Bedroom"})
    assert res.status_code == 201
    room = res.json()
    assert room["name"] == "Bedroom"
    assert room["image_url"] is None
    room_id = room["id"]

    # 2. List rooms
    res = client.get("/api/rooms")
    assert res.status_code == 200
    rooms = res.json()
    assert len(rooms) == 1
    assert rooms[0]["id"] == room_id

    # 3. Get room detail
    res = client.get(f"/api/rooms/{room_id}")
    assert res.status_code == 200
    detail = res.json()
    assert detail["id"] == room_id
    assert detail["cabinets"] == []
    assert detail["items"] == []

    # 4. Update room name
    res = client.put(f"/api/rooms/{room_id}", json={"name": "Master Bedroom"})
    assert res.status_code == 200
    assert res.json()["name"] == "Master Bedroom"

    # 5. Upload room image
    file_content = b"fake image content"
    res = client.post(
        f"/api/rooms/{room_id}/image",
        files={"image": ("room.jpg", file_content, "image/jpeg")}
    )
    assert res.status_code == 200
    assert res.json()["image_url"].startswith("/uploads/rooms/")

    # 6. Delete room
    res = client.delete(f"/api/rooms/{room_id}")
    assert res.status_code == 200
    assert client.get(f"/api/rooms/{room_id}").status_code == 404
