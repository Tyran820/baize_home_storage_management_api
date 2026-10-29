from typing import Optional
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Query, status
from pydantic import BaseModel
from bson import ObjectId
from app.database import get_db
from app.utils import save_uploaded_file, format_doc
from app.routers.rooms import get_id_filter, parse_id

router = APIRouter(prefix="/api/cabinets", tags=["Cabinets"])

class CabinetUpdateSchema(BaseModel):
    name: Optional[str] = None
    room_id: Optional[str] = None

@router.post("", status_code=status.HTTP_201_CREATED)
def create_cabinet(
    name: str = Form(...),
    room_id: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    db = get_db()
    room = db.rooms.find_one(get_id_filter(room_id))
    if not room:
        raise HTTPException(status_code=404, detail="Parent room not found")

    actual_room_id = str(room["_id"])
    image_url = None
    if image and image.filename:
        image_url = save_uploaded_file(image, subfolder="cabinets")

    cabinet_doc = {
        "name": name,
        "room_id": actual_room_id,
        "image_url": image_url
    }
    result = db.cabinets.insert_one(cabinet_doc)
    cabinet_doc["_id"] = str(result.inserted_id) if result.inserted_id else cabinet_doc.get("_id")
    return format_doc(cabinet_doc)

@router.get("")
def list_cabinets():
    db = get_db()
    cabinets = list(db.cabinets.find({}))
    return [format_doc(c) for c in cabinets]

@router.get("/{cabinet_id}")
def get_cabinet_detail(cabinet_id: str):
    db = get_db()
    cabinet = db.cabinets.find_one(get_id_filter(cabinet_id))
    if not cabinet:
        raise HTTPException(status_code=404, detail="Cabinet not found")

    formatted_cabinet = format_doc(cabinet)
    actual_cabinet_id = formatted_cabinet["id"]
    room_id = formatted_cabinet.get("room_id")

    # Get parent room info
    room_info = None
    if room_id:
        room = db.rooms.find_one(get_id_filter(room_id))
        if room:
            room_info = format_doc(room)

    # Get items in cabinet
    items = list(db.items.find({"cabinet_ids": {"$in": [actual_cabinet_id, cabinet_id]}}))
    formatted_items = [format_doc(i) for i in items]

    formatted_cabinet["room"] = room_info
    formatted_cabinet["items"] = formatted_items
    return formatted_cabinet

@router.put("/{cabinet_id}")
def update_cabinet(cabinet_id: str, cabinet_data: CabinetUpdateSchema):
    db = get_db()
    cabinet = db.cabinets.find_one(get_id_filter(cabinet_id))
    if not cabinet:
        raise HTTPException(status_code=404, detail="Cabinet not found")

    update_fields = {}
    if cabinet_data.name is not None:
        update_fields["name"] = cabinet_data.name

    if cabinet_data.room_id is not None:
        target_room = db.rooms.find_one(get_id_filter(cabinet_data.room_id))
        if not target_room:
            raise HTTPException(status_code=404, detail="Target room not found")
        update_fields["room_id"] = str(target_room["_id"])

    if update_fields:
        db.cabinets.update_one(get_id_filter(cabinet_id), {"$set": update_fields})

    updated_cabinet = db.cabinets.find_one(get_id_filter(cabinet_id))
    return format_doc(updated_cabinet)

@router.post("/{cabinet_id}/image")
def upload_cabinet_image(cabinet_id: str, image: UploadFile = File(...)):
    db = get_db()
    cabinet = db.cabinets.find_one(get_id_filter(cabinet_id))
    if not cabinet:
        raise HTTPException(status_code=404, detail="Cabinet not found")

    image_url = save_uploaded_file(image, subfolder="cabinets")
    db.cabinets.update_one(get_id_filter(cabinet_id), {"$set": {"image_url": image_url}})

    updated_cabinet = db.cabinets.find_one(get_id_filter(cabinet_id))
    return format_doc(updated_cabinet)

@router.delete("/{cabinet_id}")
def delete_cabinet(cabinet_id: str, cascade: bool = Query(False)):
    db = get_db()
    cabinet = db.cabinets.find_one(get_id_filter(cabinet_id))
    if not cabinet:
        raise HTTPException(status_code=404, detail="Cabinet not found")

    actual_cabinet_id = str(cabinet["_id"])

    # Check items in this cabinet
    items_in_cab = list(db.items.find({"cabinet_ids": {"$in": [actual_cabinet_id, cabinet_id]}}))

    # Check if removing this cabinet leaves any item with 0 cabinets
    if items_in_cab and not cascade:
        invalid_items = [
            format_doc(item)["name"]
            for item in items_in_cab
            if len(set(item.get("cabinet_ids", [])) - {actual_cabinet_id, cabinet_id}) == 0
        ]
        if invalid_items:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete cabinet because items would be left without a cabinet: {', '.join(invalid_items)}. Move items first or set cascade=true."
            )

    # If cascade or safe to remove
    for item in items_in_cab:
        item_id = item["_id"]
        remaining_cab_ids = [cid for cid in item.get("cabinet_ids", []) if cid not in (actual_cabinet_id, cabinet_id)]
        if not remaining_cab_ids:
            # Delete item if no cabinet left
            db.items.delete_one({"_id": item_id})
        else:
            db.items.update_one({"_id": item_id}, {"$set": {"cabinet_ids": remaining_cab_ids}})

    db.cabinets.delete_one(get_id_filter(cabinet_id))
    return {"message": "Cabinet deleted successfully", "cabinet_id": cabinet_id}
