import os
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.utils import ensure_upload_dir
from app.routers import rooms, cabinets, items
from app.database import get_db

app = FastAPI(
    title="Home Storage Management Microservice",
    description="Microservice for managing home rooms, storage cabinets, and stored items.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Enable CORS for microservice gateway and frontend compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

upload_dir = ensure_upload_dir()
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

app.include_router(rooms.router)
app.include_router(cabinets.router)
app.include_router(items.router)

@app.get("/", summary="Root status", tags=["Health & Status"])
def read_root():
    return {
        "service": "Home Storage Management Microservice",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health", summary="Health check endpoint for API Gateway / Traefik", tags=["Health & Status"])
def health_check():
    db_status = "ok"
    try:
        db = get_db()
        db.command("ping")
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "database": db_status
    }
