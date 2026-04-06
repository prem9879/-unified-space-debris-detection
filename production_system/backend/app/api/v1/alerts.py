from fastapi import APIRouter, Depends

from app.core.security import require_role
from app.schemas.alerts import AlertRequest, AlertResponse
from app.services.alert_service import AlertService


router = APIRouter()
_service = AlertService()


@router.post("/trigger", response_model=AlertResponse)
async def trigger_alert(
    payload: AlertRequest,
    _: dict = Depends(require_role({"admin", "analyst"})),
) -> AlertResponse:
    event = _service.trigger(channel=payload.channel, risk=payload.risk, message=payload.message)
    return AlertResponse(**event)


@router.get("/history")
async def alert_history(_: dict = Depends(require_role({"admin", "analyst", "viewer"}))) -> dict:
    return {"events": _service.list_history()}
