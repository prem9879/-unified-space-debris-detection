from pydantic import BaseModel, Field


class AlertRequest(BaseModel):
    channel: str = Field(description="email|sms|slack|discord")
    risk: float = Field(ge=0.0, le=1.0)
    message: str


class AlertResponse(BaseModel):
    id: str
    timestamp: str
    channel: str
    risk: float
    message: str
    status: str
