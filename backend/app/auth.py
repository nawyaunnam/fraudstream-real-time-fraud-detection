from datetime import datetime, timedelta, timezone

from fastapi import Header, HTTPException
from jose import JWTError, jwt

from .config import settings


def create_token(subject: str, role: str = "analyst") -> str:
    claims = {"sub": subject, "role": role, "exp": datetime.now(timezone.utc) + timedelta(hours=8)}
    return jwt.encode(claims, settings.jwt_secret, algorithm="HS256")


def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    try:
        return jwt.decode(authorization[7:], settings.jwt_secret, algorithms=["HS256"])
    except JWTError as exc:
        raise HTTPException(401, "Invalid token") from exc

