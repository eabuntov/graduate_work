from functools import wraps

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import UUID

from models.db_models import User
from models.models import RoleType
from services.token_service import TokenService
from services.user_service import UserService
from dependencies import get_token_service, get_user_service


class AuthBearer(HTTPBearer):
    async def __call__(self, request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if not credentials or credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme.",
            )
        return credentials.credentials


auth_bearer = AuthBearer()


async def get_current_user(
    token: str = Depends(auth_bearer),
    tokens: TokenService = Depends(get_token_service),
    users: UserService = Depends(get_user_service),
):
    payload = tokens.verify_access(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload.")

    user = await users.repo.get_by_id(UUID(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")

    return user


def require_permissions(required: list[str]):
    def checker(
        current_user=Depends(get_current_user),
        users: UserService = Depends(get_user_service),
    ):
        permissions = users.get_user_permissions(current_user)

        # Superuser bypass
        if current_user.is_superuser:
            return True

        for perm in required:
            if perm not in permissions:
                raise HTTPException(
                    status_code=403,
                    detail=f"Missing required permission: {perm}",
                )
        return True

    return checker


async def require_subscription(sub_type: str):
    async def checker(
        current_user=Depends(get_current_user),
        users: UserService = Depends(get_user_service),
    ):
        subs = await users.get_user_subscriptions(current_user)
        if sub_type not in subs:
            raise HTTPException(status_code=403, detail="Subscription required.")
        return True

    return checker


def role_types_required(allowed_types: list[RoleType]):
    """
    Restrict route access to users that have at least one role
    with a type from allowed_types.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # FastAPI injects current_user explicitly through dependencies
            user: User = kwargs.get("current_user")

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            # Extract role types of this user
            user_role_types = {role.type for role in getattr(user, "roles", [])}

            # Check for intersection with allowed types
            if not any(role_type in user_role_types for role_type in allowed_types):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to access this resource",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
