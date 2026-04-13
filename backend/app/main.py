import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import curves

app = FastAPI(title="Commodity Forward Curve API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(curves.router)

# In production, serve the built frontend from the same process.
# Set CURVE_STATIC_DIR to the frontend/dist path to enable.
_static_dir = os.environ.get("CURVE_STATIC_DIR")
if _static_dir and Path(_static_dir).is_dir():
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="frontend")
