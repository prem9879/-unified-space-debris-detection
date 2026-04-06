from fastapi import APIRouter, Depends

from app.core.security import require_role
from app.schemas.trajectory import TrajectoryRequest, TrajectoryResponse
from app.services.trajectory_service import TrajectoryService


router = APIRouter()
_service = TrajectoryService()


@router.post("/predict", response_model=TrajectoryResponse)
async def predict(payload: TrajectoryRequest, _: dict = Depends(require_role({"admin", "analyst"}))) -> TrajectoryResponse:
    return _service.predict(payload)
