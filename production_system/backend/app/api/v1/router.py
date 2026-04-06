from fastapi import APIRouter

from app.api.v1 import endpoints


router = APIRouter()
router.include_router(endpoints.auth.router, prefix="/auth", tags=["auth"])
router.include_router(endpoints.detection.router, prefix="/detection", tags=["detection"])
router.include_router(endpoints.collision.router, prefix="/collision", tags=["collision"])
router.include_router(endpoints.alerts.router, prefix="/alerts", tags=["alerts"])
router.include_router(endpoints.models.router, prefix="/models", tags=["models"])
router.include_router(endpoints.monitoring.router, prefix="/monitoring", tags=["monitoring"])
router.include_router(endpoints.reports.router, prefix="/reports", tags=["reports"])
router.include_router(endpoints.sources.router, prefix="/sources", tags=["sources"])
router.include_router(endpoints.trajectory.router, prefix="/trajectory", tags=["trajectory"])
router.include_router(endpoints.streams.router, prefix="/streams", tags=["streams"])
