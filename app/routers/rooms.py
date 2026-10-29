from typing import Optional, List
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Query, status
from pydantic import BaseModel
from bson import ObjectId, errors as bson_errors
from app.database import get_db
from app.utils import save_uploaded_file, format_doc

router = APIRouter(prefix="/api/rooms", tags=["Rooms"])

def parse_id(id_str: str):
    try:
        return ObjectId(id_str)
    except Exception:
        return id_str

def get_id_filter(id_str: str):
    parsed = parse_id(id_str)
    if isinstance(parsed, ObjectId):
        return {"$or": [{"_id": parsed}, {"_id": id_str}]}
    return {"_id": id_str}

class RoomUpdateSchema(BaseModel):
    name: Optional[str] = None

@router.post("", status_code=status.HTTP_201_CREATED)
def create_room(
    name: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    db = get_db()
    image_url = None
    if image and image.filename:
        image_url = save_uploaded_file(image, subfolder="rooms")

    room_doc = {
        "name": name,
        "image_url": image_url
    }
    result = db.rooms.insert_one(room_doc)
    room_doc["_id"] = str(result.inserted_id) if result.inserted_id else room_doc.get("_id")
    return format_doc(room_doc)

@router.get("")
def list_rooms():
    db = get_db()
    rooms = list(db.rooms.find({}))
    return [format_doc(r) for r in rooms]

@router.get("/{room_id}")
def get_room_detail(room_id: str):
    db = get_db()
    room = db.rooms.find_one(get_id_filter(room_id))
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    formatted_room = format_doc(room)
    actual_room_id = formatted_room["id"]

    # Find cabinets in this room
    cabinets = list(db.cabinets.find({"$or": [{"room_id": actual_room_id}, {"room_id": room_id}]}))
    formatted_cabinets = [format_doc(c) for c in cabinets]
    cabinet_ids = [c["id"] for c in formatted_cabinets]

    # Find all items stored in any cabinet in this room
    items = []
    if cabinet_ids:
        raw_items = list(db.items.find({"cabinet_ids": {"$in": cabinet_ids}}))
        items = [format_doc(i) for i in raw_items]

    formatted_room["cabinets"] = formatted_cabinets
    formatted_room["items"] = items
    return formatted_room

@router.put("/{room_id}")
def update_room(room_id: str, room_data: RoomUpdateSchema):
    db = get_db()
    room = db.rooms.find_one(get_id_filter(room_id))
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    update_fields = {}
    if room_data.name is not None:
        update_fields["name"] = room_data.name

    if update_fields:
        db.rooms.update_one(get_id_filter(room_id), {"$set": update_fields})

    updated_room = db.rooms.find_one(get_id_filter(room_id))
    return format_doc(updated_room)

@router.post("/{room_id}/image")
def upload_room_image(room_id: str, image: UploadFile = File(...)):
    db = get_db()
    room = db.rooms.find_one(get_id_filter(room_id))
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    image_url = save_uploaded_file(image, subfolder="rooms")
    db.rooms.update_one(get_id_filter(room_id), {"$set": {"image_url": image_url}})

    updated_room = db.rooms.find_one(get_id_filter(room_id))
    return format_doc(updated_room)

@router.delete("/{room_id}")
def delete_room(room_id: str, cascade: bool = Query(False)):
    db = get_db()
    room = db.rooms.find_one(get_id_filter(room_id))
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    actual_room_id = str(room["_id"])
    cabinets = list(db.cabinets.find({"$or": [{"room_id": actual_room_id}, {"room_id": room_id}]}))

    if cabinets and not cascade:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete room that contains cabinets. Move or delete cabinets first, or set cascade=true."
        )

    if cabinets and cascade:
        cabinet_ids = [str(c["_id"]) for c in cabinets]
        db.cabinets.delete_many({"_id": {"$in": [parse_id(cid) for cid in cabinet_ids] + cabinet_ids}})
        # Update items referencing deleted cabinets
        for cid in cabinet_ids:
            db.items.update_many(
                {"cabinet_ids": cid},
                {"$pull": {"cabinet_ids": cid}}
            )

    db.rooms.delete_one(get_id_filter(room_id))
    return {"message": "Room deleted successfully", "room_id": room_id}
