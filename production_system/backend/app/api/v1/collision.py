from fastapi import APIRouter, Depends

from app.core.rate_limit import enforce_rate_limit
from app.core.security import require_role
from app.schemas.collision import CollisionRequest, CollisionResponse
from app.services.collision_service import CollisionService


router = APIRouter(dependencies=[Depends(enforce_rate_limit)])
_service = CollisionService()


@router.post("/assess", response_model=CollisionResponse)
async def assess_collision(
    payload: CollisionRequest,
    _: dict = Depends(require_role({"admin", "analyst"})),
) -> CollisionResponse:
    return _service.assess(payload)
