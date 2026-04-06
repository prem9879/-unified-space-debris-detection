from pydantic import BaseModel


class TrajectoryPoint(BaseModel):
    t_s: float
    x_km: float
    y_km: float
    z_km: float


class TrajectoryRequest(BaseModel):
    object_id: str
    history: list[TrajectoryPoint]
    horizon_s: int = 600


class TrajectoryResponse(BaseModel):
    object_id: str
    method: str
    predicted: list[TrajectoryPoint]
    uncertainty_band_km: float
