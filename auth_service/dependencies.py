from typing import AsyncGenerator

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from fastapi import Depends, HTTPException, status

from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

from repositories.login_history_repository import LoginHistoryRepository
from repositories.user_repository import UserRepository
from repositories.roles_repository import RoleRepository
from repositories.subscription_repository import SubscriptionRepository
from security.password import PasswordHasher
from services.login_history_service import LoginHistoryService
from services.user_service import UserService
from services.role_service import RoleService
from services.subscription_service import SubscriptionService
from services.token_service import TokenService
from security.jwt_routines import JWTHandler


from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from config.settings import settings


# Create PostgreSQL async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=bool(settings.db_echo),
)

# SQLAlchemyInstrumentor().instrument(
#     engine=engine,
#     enable_commenter=True,
#     commenter_options={"db_driver": True},
# )

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


# Dependency for FastAPI
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_redis() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_user_repo(session: AsyncSession = Depends(get_session)) -> UserRepository:
    return UserRepository(session)


def get_role_repo(session: AsyncSession = Depends(get_session)) -> RoleRepository:
    return RoleRepository(session)


def get_subscription_repo(
    session: AsyncSession = Depends(get_session),
) -> SubscriptionRepository:
    return SubscriptionRepository(session)


def get_user_service(
    session: AsyncSession = Depends(get_session),
):
    user_repo = UserRepository(session)
    role_repo = RoleRepository(session)
    hasher = PasswordHasher()
    return UserService(
        repo=user_repo,
        hasher=hasher,
        role_repo=role_repo,
        default_role_name="user",
    )


def get_role_service(repo: RoleRepository = Depends(get_role_repo)) -> RoleService:
    return RoleService(repo)


def get_subscription_service(
    repo: SubscriptionRepository = Depends(get_subscription_repo),
) -> SubscriptionService:
    return SubscriptionService(repo)


def get_token_service(
    redis: Redis = Depends(get_redis),
    user_repo: UserRepository = Depends(get_user_repo),
) -> TokenService:
    return TokenService(JWTHandler())


def get_login_history_service(
    session: AsyncSession = Depends(get_session),
) -> LoginHistoryService:
    repo = LoginHistoryRepository(session)
    return LoginHistoryService(repo)


auth_scheme = HTTPBearer(auto_error=False)


async def require_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    tokens: TokenService = Depends(get_token_service),
    users: UserService = Depends(get_user_service),
):
    """
    Ensures the user is authenticated by verifying the JWT access token.
    Returns the User instance if valid.
    """

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    token = credentials.credentials

    payload = tokens.verify_access(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")

    user = await users.repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user
