from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import curves

app = FastAPI(title="Commodity Forward Curve API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(curves.router)
