from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, status, Body
from pydantic import BaseModel, Field
from bson import ObjectId
from app.database import get_db
from app.utils import save_uploaded_file, format_doc
from app.routers.rooms import get_id_filter, parse_id

router = APIRouter(prefix="/api/items", tags=["Items"])

class ItemCreateSchema(BaseModel):
    name: str
    cabinet_ids: List[str] = Field(..., min_length=1, description="List of cabinet IDs where item is stored")

class ItemUpdateSchema(BaseModel):
    name: Optional[str] = None
    cabinet_ids: Optional[List[str]] = None

@router.post("", status_code=status.HTTP_201_CREATED)
def create_item(item_data: ItemCreateSchema):
    db = get_db()
    if not item_data.cabinet_ids:
        raise HTTPException(status_code=400, detail="Item must belong to at least one cabinet")

    # Validate all cabinet_ids exist
    valid_cabinet_ids = []
    for cab_id in item_data.cabinet_ids:
        cab = db.cabinets.find_one(get_id_filter(cab_id))
        if not cab:
            raise HTTPException(status_code=404, detail=f"Cabinet with ID '{cab_id}' not found")
        valid_cabinet_ids.append(str(cab["_id"]))

    item_doc = {
        "name": item_data.name,
        "cabinet_ids": list(set(valid_cabinet_ids)),
        "cabinet_images": {}  # mapping cabinet_id -> image_url
    }
    result = db.items.insert_one(item_doc)
    item_doc["_id"] = str(result.inserted_id) if result.inserted_id else item_doc.get("_id")
    return format_doc(item_doc)

@router.get("")
def list_items():
    db = get_db()
    items = list(db.items.find({}))
    return [format_doc(i) for i in items]

@router.get("/{item_id}")
def get_item_detail(item_id: str):
    db = get_db()
    item = db.items.find_one(get_id_filter(item_id))
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    formatted_item = format_doc(item)
    cab_ids = formatted_item.get("cabinet_ids", [])
    cabinet_images = formatted_item.get("cabinet_images", {})

    # Fetch associated cabinets
    cabinets = []
    rooms_dict = {}
    storage_images = []

    for cab_id in cab_ids:
        cab = db.cabinets.find_one(get_id_filter(cab_id))
        if cab:
            formatted_cab = format_doc(cab)
            cabinets.append(formatted_cab)

            # Fetch parent room if available
            room_id = formatted_cab.get("room_id")
            if room_id and room_id not in rooms_dict:
                room = db.rooms.find_one(get_id_filter(room_id))
                if room:
                    rooms_dict[room_id] = format_doc(room)

            # Get storage image for this cabinet
            img_url = cabinet_images.get(formatted_cab["id"]) or cabinet_images.get(cab_id)
            storage_images.append({
                "cabinet_id": formatted_cab["id"],
                "cabinet_name": formatted_cab.get("name"),
                "image_url": img_url
            })

    formatted_item["cabinets"] = cabinets
    formatted_item["rooms"] = list(rooms_dict.values())
    formatted_item["storage_images"] = storage_images
    return formatted_item

@router.put("/{item_id}")
def update_item(item_id: str, item_data: ItemUpdateSchema):
    db = get_db()
    item = db.items.find_one(get_id_filter(item_id))
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    update_fields = {}
    if item_data.name is not None:
        update_fields["name"] = item_data.name

    if item_data.cabinet_ids is not None:
        if len(item_data.cabinet_ids) == 0:
            raise HTTPException(status_code=400, detail="Item must belong to at least one cabinet")

        valid_cabinet_ids = []
        for cab_id in item_data.cabinet_ids:
            cab = db.cabinets.find_one(get_id_filter(cab_id))
            if not cab:
                raise HTTPException(status_code=404, detail=f"Cabinet with ID '{cab_id}' not found")
            valid_cabinet_ids.append(str(cab["_id"]))

        update_fields["cabinet_ids"] = list(set(valid_cabinet_ids))

    if update_fields:
        db.items.update_one(get_id_filter(item_id), {"$set": update_fields})

    updated_item = db.items.find_one(get_id_filter(item_id))
    return format_doc(updated_item)

@router.post("/{item_id}/images/{cabinet_id}")
def upload_item_storage_image(
    item_id: str,
    cabinet_id: str,
    image: UploadFile = File(...)
):
    db = get_db()
    item = db.items.find_one(get_id_filter(item_id))
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    cab = db.cabinets.find_one(get_id_filter(cabinet_id))
    if not cab:
        raise HTTPException(status_code=404, detail="Cabinet not found")

    actual_cabinet_id = str(cab["_id"])
    item_cab_ids = item.get("cabinet_ids", [])

    if actual_cabinet_id not in item_cab_ids and cabinet_id not in item_cab_ids:
        raise HTTPException(status_code=400, detail="Item is not stored in the specified cabinet")

    image_url = save_uploaded_file(image, subfolder="items")

    cabinet_images = item.get("cabinet_images", {})
    cabinet_images[actual_cabinet_id] = image_url

    db.items.update_one(get_id_filter(item_id), {"$set": {"cabinet_images": cabinet_images}})

    updated_item = db.items.find_one(get_id_filter(item_id))
    return format_doc(updated_item)

@router.delete("/{item_id}")
def delete_item(item_id: str):
    db = get_db()
    item = db.items.find_one(get_id_filter(item_id))
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.items.delete_one(get_id_filter(item_id))
    return {"message": "Item deleted successfully", "item_id": item_id}
