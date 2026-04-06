from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import require_role
from app.services.external_sources import ExternalSourceService


class SyntheticRequest(BaseModel):
    scenes: int = 20


router = APIRouter()
_service = ExternalSourceService()


@router.get("/tle")
async def pull_tle(_: dict = Depends(require_role({"admin", "analyst"}))) -> dict:
    return _service.pull_tle_snapshot()


@router.get("/esa-optical")
async def pull_esa(_: dict = Depends(require_role({"admin", "analyst"}))) -> dict:
    return _service.pull_esa_optical_feed()


@router.post("/synthetic")
async def synthetic_job(payload: SyntheticRequest, _: dict = Depends(require_role({"admin", "analyst"}))) -> dict:
    return _service.synthetic_blender_job(payload.scenes)
