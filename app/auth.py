from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Request
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .models import User

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_token(user: User) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": str(user.id), "role": user.role, "exp": expires}, settings.secret_key, algorithm="HS256")


def current_user(request: Request, db: Session) -> User | None:
    token = request.cookies.get("access_token")
    authorization = request.headers.get("Authorization", "")
    if not token and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ")
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return db.scalar(select(User).where(User.id == int(payload["sub"])))
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
