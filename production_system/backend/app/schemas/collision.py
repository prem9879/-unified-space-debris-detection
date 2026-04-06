from pydantic import BaseModel, Field


class CollisionRequest(BaseModel):
    object_a: str
    object_b: str
    position_a_km: list[float]
    velocity_a_km_s: list[float]
    position_b_km: list[float]
    velocity_b_km_s: list[float]


class CollisionResponse(BaseModel):
    closest_approach_km: float
    time_to_impact_s: float
    collision_probability: float = Field(ge=0.0, le=1.0)
    suggested_maneuver: str
