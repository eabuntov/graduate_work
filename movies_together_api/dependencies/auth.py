import json
import logging

from fastapi import Depends, HTTPException, Request, WebSocket
from fastapi.security import HTTPAuthorizationCredentials
import jwt
from dependencies.security import bearer_scheme
from dependencies.auth_settings import settings


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    if credentials is None:
        return {}

    token = credentials.credentials

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


async def require_user_ws(websocket: WebSocket) -> tuple:
    access_token = websocket.cookies.get("access_token")

    if not access_token:
        logging.debug("No access token")
        raise HTTPException(
            status_code=303,
            headers={"Location": f"/auth/login?next={websocket.url.path}"},
        )

    try:
        payload = jwt.decode(
            access_token,
            settings.JWT_ACCESS_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options=json.loads(settings.jwt_options.replace("'",'"')),
        )
        logging.debug(payload)

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            raise jwt.PyJWTError("Invalid token payload")

        websocket.state.user_id = str(user_id)

        return user_id, email

    except jwt.ExpiredSignatureError as e:
        logging.error(e)
        raise HTTPException(
            status_code=303,
            headers={"Location": f"/auth/login?next={websocket.url.path}"},
        )

    except jwt.PyJWTError as e:
        logging.error(e)
        raise HTTPException(
            status_code=303,
            headers={"Location": f"/auth/login?next={websocket.url.path}"},
        )


async def require_user(request: Request) -> tuple:
    access_token = request.cookies.get("access_token")

    if not access_token:
        logging.debug("No access token")
        raise HTTPException(
            status_code=303,
            headers={"Location": f"/auth/login?next={request.url.path}"},
        )

    try:
        payload = jwt.decode(
            access_token,
            settings.JWT_ACCESS_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options=json.loads(settings.jwt_options.replace("'",'"')),
        )
        logging.debug(payload)

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            raise jwt.PyJWTError("Invalid token payload")

        request.state.user_id = str(user_id)

        return user_id, email

    except jwt.ExpiredSignatureError as e:
        logging.error(e)
        raise HTTPException(
            status_code=303,
            headers={"Location": f"/auth/login?next={request.url.path}"},
        )

    except jwt.PyJWTError as e:
        logging.error(e)
        raise HTTPException(
            status_code=303,
            headers={"Location": f"/auth/login?next={request.url.path}"},
        )
