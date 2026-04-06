from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import require_role
from app.services.model_registry import ModelRegistryService


class PromoteRequest(BaseModel):
    name: str
    version: str


router = APIRouter()
_registry = ModelRegistryService()


@router.get("/")
async def list_models(_: dict = Depends(require_role({"admin", "analyst", "viewer"}))) -> dict:
    return {"models": _registry.list_models()}


@router.post("/promote")
async def promote(payload: PromoteRequest, _: dict = Depends(require_role({"admin"}))) -> dict:
    try:
        model = _registry.promote(payload.name, payload.version)
        return {"promoted": model}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
