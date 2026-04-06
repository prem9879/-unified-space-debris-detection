from pydantic import BaseModel, Field


class DetectionBox(BaseModel):
    object_id: str
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox_xyxy: list[float]
    velocity_m_s: float
    size_cm: float
    uncertainty: float = Field(ge=0.0, le=1.0)


class DetectionResponse(BaseModel):
    frame_id: str
    modality: str
    fps_estimate: float
    detections: list[DetectionBox]
    segmentation_mask_uri: str | None = None
    heatmap_uri: str | None = None
    attention_map_uri: str | None = None
    model_registry: dict[str, dict[str, object]] | None = None
