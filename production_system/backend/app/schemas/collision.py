from pydantic import BaseModel, Field


class CollisionHistoryPoint(BaseModel):
    t_s: float
    x_km: float
    y_km: float
    z_km: float


class CollisionRequest(BaseModel):
    object_a: str
    object_b: str
    position_a_km: list[float]
    velocity_a_km_s: list[float]
    position_b_km: list[float]
    velocity_b_km_s: list[float]
    ai_forecast_horizon_s: int = Field(default=1800, ge=60, le=86400)
    ai_risk_weight: float = Field(default=0.35, ge=0.0, le=1.0)
    history_a: list[CollisionHistoryPoint] = Field(default_factory=list)
    history_b: list[CollisionHistoryPoint] = Field(default_factory=list)


class CollisionResponse(BaseModel):
    object_a: str
    object_b: str
    closest_approach_km: float
    time_to_impact_s: float
    relative_velocity_km_s: float
    physics_collision_probability: float = Field(ge=0.0, le=1.0)
    ai_collision_probability: float = Field(ge=0.0, le=1.0)
    collision_probability: float = Field(ge=0.0, le=1.0)
    risk_score: float = Field(ge=0.0, le=100.0)
    risk_level: str
    fusion_method: str
    time_to_collision_hours: float
    summary: str
    suggested_maneuver: str
