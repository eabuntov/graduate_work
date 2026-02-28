from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from redis import Redis
from sqlalchemy import UUID
from dependencies import (
    get_user_service,
    get_token_service,
    get_login_history_service,
    require_authenticated_user,
    get_redis,
)
from models.db_models import User
from models.models import (
    UserRead,
    UserCreate,
    UserLogin,
    StandardResponse,
    LoginHistoryRead,
)
from services.login_history_service import LoginHistoryService
from services.user_service import UserService
from services.token_service import TokenService

from rate_limit.rate_limiter import rate_limit

from api.v1.oauth_classes import OAuthProvider

auth_router = APIRouter(prefix="/auth", tags=["auth"], dependencies=[Depends(rate_limit("auth"))])


@auth_router.post("/register", response_model=UserRead)
async def register_user(
    data: UserCreate, users: UserService = Depends(get_user_service)
):
    return await users.register(
        email=data.email, password=data.password, full_name=data.full_name
    )


@auth_router.post("/login")
async def login_user(
    data: UserLogin,
    request: Request,
    users: UserService = Depends(get_user_service),
    tokens: TokenService = Depends(get_token_service),
    history: LoginHistoryService = Depends(get_login_history_service),
):
    user = await users.authenticate(data.email, data.password)

    if user:
        await history.record_login(
            user.id, request.client.host, request.headers.get("User-Agent")
        )
        return tokens.create_token_pair(user)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Basic"},
    )


@auth_router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    tokens: TokenService = Depends(get_token_service),
    redis: Redis = Depends(get_redis),
):
    # 1. Validate / decode refresh JWT
    try:
        payload = tokens.decode_refresh(refresh_token)
        user_id = UUID(payload.get("sub"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # 2. Check that refresh token is not revoked
    key = f"refresh:{refresh_token}"
    exists = await redis.get(key)

    if not exists:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked or expired",
        )

    # 3. Load user + roles + entitlements
    user_service = get_user_service()
    user = await user_service.repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    roles = [role.name for role in getattr(user, "roles", [])]

    # If entitlements come from subscription or user field:
    entitlements = getattr(user, "entitlements", [])

    # 4. Issue new tokens
    access, refresh = tokens.create_token_pair(user, roles, entitlements)

    # 5. Store new refresh token in Redis
    await redis.setex(f"refresh:{refresh}", tokens.refresh_expire_seconds, str(user.id))

    # Optional: remove old refresh token
    await redis.delete(key)

    return {"access_token": access, "refresh_token": refresh}


@auth_router.post("/logout", response_model=StandardResponse)
async def logout(
    refresh_token: str,
    redis: Redis = Depends(get_redis),
):
    """Revoke refresh token by removing it from Redis."""
    key = f"refresh:{refresh_token}"

    deleted = await redis.delete(key)

    if deleted == 0:
        raise HTTPException(status_code=400, detail="Token already revoked or invalid")

    return {"detail": "Logged out"}


@auth_router.get("/login-history", response_model=list[LoginHistoryRead])
async def get_login_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    current_user: User = Depends(require_authenticated_user),
    history: LoginHistoryService = Depends(get_login_history_service),
):
    offset = (page - 1) * page_size

    return await history.get_user_history(
        user_id=current_user.id,
        limit=page_size,
        offset=offset,
    )

@auth_router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(require_authenticated_user)):
    return current_user

templates = Jinja2Templates(directory="templates")

@auth_router.get("/login", response_class=HTMLResponse)
async def login_oauth(
request: Request
):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )

@auth_router.get("/oauth/{provider}")
async def oauth_login(provider: str, request: Request):
    oauth = OAuthProvider.get_provider(provider)

    redirect_uri = str(request.url_for("oauth_callback", provider=provider))
    return {
        "authorize_url": oauth.get_authorize_url(redirect_uri)
    }


@auth_router.post("/login-form")
async def login_form(
    email: str = Form(...),
    password: str = Form(...),
    request: Request = None,
    users: UserService = Depends(get_user_service),
    tokens: TokenService = Depends(get_token_service),
    history: LoginHistoryService = Depends(get_login_history_service),
):
    user = await users.authenticate(email, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    await history.record_login(
        user.id, request.client.host, request.headers.get("User-Agent")
    )

    return tokens.create_token_pair(user)

@auth_router.get("/oauth/{provider}/callback", name="oauth_callback")
async def oauth_callback(
    provider: str,
    code: str,
    request: Request,
    users: UserService = Depends(get_user_service),
    tokens: TokenService = Depends(get_token_service),
):
    oauth = OAuthProvider.get_provider(provider)

    redirect_uri = str(request.url_for("oauth_callback", provider=provider))

    token_data = await oauth.exchange_code(code, redirect_uri)
    access_token = token_data["access_token"]

    profile = await oauth.fetch_userinfo(access_token)

    user = await users.get_or_create_oauth_user(
        provider=provider,
        provider_id=profile.get("id"),
        email=profile.get("email"),
        full_name=profile.get("name"),
    )

    access, refresh = tokens.create_token_pair(user)
    return {"access_token": access, "refresh_token": refresh}
