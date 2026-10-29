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

def test_item_crud_multi_cabinet_and_storage_images():
    # Setup room and cabinets
    r1 = client.post("/api/rooms", data={"name": "Storage Room"}).json()
    r2 = client.post("/api/rooms", data={"name": "Balcony"}).json()

    c1 = client.post("/api/cabinets", data={"name": "Cabinet A", "room_id": r1["id"]}).json()
    c2 = client.post("/api/cabinets", data={"name": "Cabinet B", "room_id": r1["id"]}).json()
    c3 = client.post("/api/cabinets", data={"name": "Cabinet C", "room_id": r2["id"]}).json()

    # 1. Create item belonging to multiple cabinets (Cabinet A & Cabinet C)
    res = client.post("/api/items", json={
        "name": "Screwdriver Set",
        "cabinet_ids": [c1["id"], c3["id"]],
        "quantity": 5
    })
    assert res.status_code == 201
    item = res.json()
    assert item["name"] == "Screwdriver Set"
    assert item["quantity"] == 5
    assert "created_at" in item
    assert set(item["cabinet_ids"]) == {c1["id"], c3["id"]}
    item_id = item["id"]

    # 2. List items
    res = client.get("/api/items")
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 3. Upload storage image for Cabinet A
    res = client.post(
        f"/api/items/{item_id}/images/{c1['id']}",
        files={"image": ("c1_item.jpg", b"screwdriver in cabinet A", "image/jpeg")}
    )
    assert res.status_code == 200

    # Upload storage image for Cabinet C
    res = client.post(
        f"/api/items/{item_id}/images/{c3['id']}",
        files={"image": ("c3_item.jpg", b"screwdriver in cabinet C", "image/jpeg")}
    )
    assert res.status_code == 200

    # 4. Query item detail
    res = client.get(f"/api/items/{item_id}")
    assert res.status_code == 200
    detail = res.json()
    assert detail["quantity"] == 5
    assert len(detail["cabinets"]) == 2
    assert len(detail["rooms"]) == 2
    assert len(detail["storage_images"]) == 2

    # Check that storage images exist for both cabinets
    cab_imgs = {img["cabinet_id"]: img["image_url"] for img in detail["storage_images"]}
    assert cab_imgs[c1["id"]].startswith("/uploads/items/")
    assert cab_imgs[c3["id"]].startswith("/uploads/items/")

    # 5. Query room detail for Storage Room (r1)
    res = client.get(f"/api/rooms/{r1['id']}")
    assert res.status_code == 200
    r1_detail = res.json()
    assert len(r1_detail["cabinets"]) == 2
    assert len(r1_detail["items"]) == 1
    assert r1_detail["items"][0]["name"] == "Screwdriver Set"

    # 6. Query cabinet detail for Cabinet C (c3)
    res = client.get(f"/api/cabinets/{c3['id']}")
    assert res.status_code == 200
    c3_detail = res.json()
    assert len(c3_detail["items"]) == 1
    assert c3_detail["items"][0]["name"] == "Screwdriver Set"

    # 7. Move item to Cabinet B only and update quantity
    res = client.put(f"/api/items/{item_id}", json={
        "cabinet_ids": [c2["id"]],
        "quantity": 3
    })
    assert res.status_code == 200
    updated_item = res.json()
    assert updated_item["cabinet_ids"] == [c2["id"]]
    assert updated_item["quantity"] == 3

    # 8. Delete item
    res = client.delete(f"/api/items/{item_id}")
    assert res.status_code == 200
    assert client.get(f"/api/items/{item_id}").status_code == 404
