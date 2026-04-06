from fastapi import APIRouter, HTTPException

from app.core.security import authenticate_user, create_access_token
from app.schemas.auth import TokenRequest, TokenResponse


router = APIRouter()


@router.post("/token", response_model=TokenResponse)
async def issue_token(payload: TokenRequest) -> TokenResponse:
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(subject=user["username"], role=user["role"])
    return TokenResponse(access_token=token, role=user["role"])
