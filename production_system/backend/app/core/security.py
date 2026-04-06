from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


_FAKE_USERS = {
    "admin": {"username": "admin", "password": "admin123", "role": "admin"},
    "analyst": {"username": "analyst", "password": "analyst123", "role": "analyst"},
    "viewer": {"username": "viewer", "password": "viewer123", "role": "viewer"},
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    user = _FAKE_USERS.get(username)
    if not user:
        return None
    if password != user["password"]:
        return None
    return user


def create_access_token(subject: str, role: str, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes or settings.jwt_expire_minutes)
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        username = payload.get("sub")
        role = payload.get("role")
        if not username or not role:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc
    return {"username": username, "role": role}


def require_role(allowed_roles: set[str]):
    async def _role_guard(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return _role_guard
