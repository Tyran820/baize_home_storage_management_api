import os
import uuid
from fastapi import UploadFile

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

def ensure_upload_dir(subfolder: str = "") -> str:
    path = os.path.join(UPLOAD_DIR, subfolder)
    os.makedirs(path, exist_ok=True)
    return path

def save_uploaded_file(file: UploadFile, subfolder: str = "") -> str:
    dir_path = ensure_upload_dir(subfolder)
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
    filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(dir_path, filename)

    with open(file_path, "wb") as f:
        content = file.file.read()
        f.write(content)

    relative_path = f"/uploads/{subfolder}/{filename}" if subfolder else f"/uploads/{filename}"
    return relative_path

def format_doc(doc: dict) -> dict:
    if not doc:
        return doc
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc
