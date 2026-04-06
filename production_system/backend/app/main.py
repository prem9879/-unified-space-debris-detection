from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.v1.router import router as v1_router
from app.core.config import get_settings


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-grade multi-modal space debris detection and collision intelligence API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix=settings.api_prefix)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get("/readyz")
async def readyz() -> dict[str, str]:
    return {"status": "ready", "environment": settings.environment}


@app.get("/metrics")
async def metrics() -> JSONResponse:
    return JSONResponse(content=generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)
