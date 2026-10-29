import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.utils import ensure_upload_dir
from app.routers import rooms, cabinets, items

app = FastAPI(title="Home Storage Management API", version="1.0.0")

upload_dir = ensure_upload_dir()
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

app.include_router(rooms.router)
app.include_router(cabinets.router)
app.include_router(items.router)

@app.get("/")
def read_root():
    return {"message": "Home Storage Management API is running"}
