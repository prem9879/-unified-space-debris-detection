from fastapi import APIRouter, Depends

from app.core.security import require_role
from app.schemas.reporting import ReportRequest, ReportResponse
from app.services.report_service import ReportService


router = APIRouter()
_service = ReportService()


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    payload: ReportRequest,
    _: dict = Depends(require_role({"admin", "analyst"})),
) -> ReportResponse:
    return _service.generate(payload)
