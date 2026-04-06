from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.rate_limit import enforce_rate_limit
from app.core.security import require_role
from app.schemas.detection import DetectionResponse
from app.schemas.trajectory import TrajectoryRequest, TrajectoryResponse
from app.services.detection_service import DetectionService
from app.services.tracking_service import TrackingService
from app.services.trajectory_service import TrajectoryService


router = APIRouter(dependencies=[Depends(enforce_rate_limit)])
_service = DetectionService()
_tracker = TrackingService(max_tracks=100)
_trajectory = TrajectoryService()


@router.post("/infer", response_model=DetectionResponse)
async def infer_image(
    modality: str = Form("optical"),
    image: UploadFile = File(...),
    _: dict = Depends(require_role({"admin", "analyst"})),
) -> DetectionResponse:
    raw = await image.read()
    result = _service.infer(raw, modality=modality)

    for det in result.detections:
        x1, y1, x2, y2 = det.bbox_xyxy
        center = [(x1 + x2) / 2.0, (y1 + y2) / 2.0]
        _tracker.update(det.object_id, center)

    return result


@router.get("/tracks")
async def tracks(_: dict = Depends(require_role({"admin", "analyst", "viewer"}))) -> dict:
    return {
        "active_tracks": len(_tracker.tracks),
        "tracks": [
            {"object_id": item.object_id, "points": len(item.history), "history": item.history[-20:]}
            for item in _tracker.tracks.values()
        ],
    }


@router.post("/infer_video")
async def infer_video(
    modality: str = Form("optical"),
    fps: int = Form(30),
    frames: int = Form(12),
    image: UploadFile = File(...),
    _: dict = Depends(require_role({"admin", "analyst"})),
) -> dict:
    raw = await image.read()
    series = []
    for _idx in range(max(1, min(frames, 30))):
        result = _service.infer(raw, modality=modality)
        series.append({
            "frame_id": result.frame_id,
            "detections": len(result.detections),
            "fps_estimate": result.fps_estimate,
        })
    return {"fps": fps, "frames": len(series), "series": series}


@router.post("/trajectory", response_model=TrajectoryResponse)
async def predict_trajectory(
    payload: TrajectoryRequest,
    _: dict = Depends(require_role({"admin", "analyst"})),
) -> TrajectoryResponse:
    return _trajectory.predict(payload)
