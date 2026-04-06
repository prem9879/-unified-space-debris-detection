from fastapi import APIRouter, Depends

from app.core.security import require_role


router = APIRouter()


@router.get("/slo")
async def slo_snapshot(_: dict = Depends(require_role({"admin", "analyst", "viewer"}))) -> dict:
    return {
        "image_detection_latency_ms_p95": 92,
        "api_latency_ms_p95": 164,
        "video_fps_min": 30,
        "uptime_sla": 99.9,
    }
