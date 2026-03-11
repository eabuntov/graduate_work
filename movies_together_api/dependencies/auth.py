import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
import jwt
from dependencies.security import bearer_scheme
from dependencies.auth_settings import settings


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    if credentials is None:
        return {}

    token = credentials
    logging.debug(f"{token=}")

    try:
        payload = jwt.decode(
            token,
            settings.JWT_ACCESS_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.AUTH_ISSUER,
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        logging.warning("Token expired")
        return {}

    return payload

def get_anonymous_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    if credentials is None:
        return None

    try:
        return jwt.decode(
            credentials.credentials,
            settings.JWT_ACCESS_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.AUTH_ISSUER,
        )
    except jwt.InvalidTokenError:
        return None

def require_role(role: str):
    def checker(user=Depends(get_current_user)):
        if role not in user.get("roles", []):
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return checker