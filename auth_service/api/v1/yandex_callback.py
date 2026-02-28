import httpx
from fastapi import Query, Depends, HTTPException
from fastapi.responses import RedirectResponse
from redis import Redis
from starlette import status

from auth_service.dependencies import get_user_service, get_token_service, get_redis
from auth_service.services.token_service import TokenService
from auth_service.services.user_service import UserService

YANDEX_TOKEN_URL = "https://oauth.yandex.ru/token"
YANDEX_USERINFO_URL = "https://login.yandex.ru/info"

YANDEX_CLIENT_ID = "YOUR_CLIENT_ID"
YANDEX_CLIENT_SECRET = "YOUR_CLIENT_SECRET"
YANDEX_REDIRECT_URI = "https://your-domain/auth/yandex/callback"


@auth_router.get("/yandex/callback")
async def yandex_callback(
    request: Request,
    code: str | None = Query(default=None),
    access_token: str | None = Query(default=None),
    error: str | None = Query(default=None),
    users: UserService = Depends(get_user_service),
    tokens: TokenService = Depends(get_token_service),
    redis: Redis = Depends(get_redis),
):
    """
    Handles OAuth redirect from Yandex with:
    - ?code=... (authorization code flow)
    - ?access_token=... (implicit flow, rare but possible)
    - ?error=...
    """

    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Yandex OAuth error: {error}",
        )

    # ------------------------------------------------------------------
    # 1. Exchange authorization code → access_token (if needed)
    # ------------------------------------------------------------------
    if not access_token and code:
        async with httpx.AsyncClient(timeout=10) as client:
            token_resp = await client.post(
                YANDEX_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": YANDEX_CLIENT_ID,
                    "client_secret": YANDEX_CLIENT_SECRET,
                    "redirect_uri": YANDEX_REDIRECT_URI,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=401,
                detail="Failed to exchange Yandex authorization code",
            )

        access_token = token_resp.json().get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=400,
            detail="No access token received from Yandex",
        )

    # ------------------------------------------------------------------
    # 2. Fetch Yandex user profile
    # ------------------------------------------------------------------
    async with httpx.AsyncClient(timeout=10) as client:
        userinfo_resp = await client.get(
            YANDEX_USERINFO_URL,
            params={"format": "json"},
            headers={"Authorization": f"OAuth {access_token}"},
        )

    if userinfo_resp.status_code != 200:
        raise HTTPException(
            status_code=401,
            detail="Failed to fetch Yandex user profile",
        )

    yandex_user = userinfo_resp.json()

    # Typical fields:
    # id, login, emails[], default_email, real_name
    yandex_id = yandex_user.get("id")
    email = yandex_user.get("default_email")
    full_name = yandex_user.get("real_name") or yandex_user.get("login")

    if not yandex_id:
        raise HTTPException(status_code=400, detail="Invalid Yandex user data")

    # ------------------------------------------------------------------
    # 3. Get or create local user
    # ------------------------------------------------------------------
    user = await users.get_or_create_oauth_user(
        provider="yandex",
        provider_id=yandex_id,
        email=email,
        full_name=full_name,
    )

    # ------------------------------------------------------------------
    # 4. Issue JWT tokens
    # ------------------------------------------------------------------
    access, refresh = tokens.create_token_pair(user)

    await redis.setex(
        f"refresh:{refresh}",
        tokens.refresh_expire_seconds,
        str(user.id),
    )

    # ------------------------------------------------------------------
    # 5. Redirect back to frontend with tokens
    # ------------------------------------------------------------------
    return RedirectResponse(
        url=f"/login/success?access={access}&refresh={refresh}",
        status_code=302,
    )
