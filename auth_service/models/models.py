"""
Сервис аутентификации и авторизации
---------------------------------------
Файл: auth_service_models.py

Этот файл содержит:
- Заметки об архитектуре высокого уровня для сервиса AuthZ на основе JWT, реализованного с помощью FastAPI.
- Модели данных Pydantic (запрос/ответ/DTO), которые API сервиса будет предоставлять.

Архитектура (краткая)
--------------------
Компоненты:
- Приложение FastAPI, предоставляющее конечные точки REST для аутентификации, жизненного цикла токенов, управления пользователями и ролями.
- Postgres (или другая реляционная база данных) для постоянного хранения пользователей, ролей, подписок и назначений.
- Redis для: списка отозванных токенов, краткосрочного кэширования и метаданных ротации токенов сеанса/обновления.
- Дополнительно: внутренняя конечная точка JWKS, предоставляющая открытый ключ (при использовании асимметричных JWT), чтобы другие сервисы могли проверять токены без обращения к службе аутентификации. сервис при каждом запросе.
– Другие сервисы (публичный API кинотеатра, панель администратора) проверяют токены доступа локально (через JWKS или общий секрет) и при необходимости вызывают службу авторизации для анализа пользователя/роли.

Ключевые решения:
– Токены доступа (JWT) имеют короткий срок жизни (например, 5–15 минут). Токены обновления имеют длительный срок жизни (дни/недели) и хранятся на стороне сервера (или отслеживается их состояние ротации), что позволяет их отзывать.
– Используйте ротацию токенов обновления для ограничения атак повторного воспроизведения. Идентификаторы токенов обновления (JTI) следует хранить в Redis с указанием состояния (действителен/отозван).
– Роли представляют собой наборы разрешений. Пользователи получают роли через назначения. Конечные точки CRUD для ролей существуют и защищены от администраторов.
– Анонимные пользователи существуют неявно: если заголовок авторизации не указан, пользователь рассматривается как «анонимная» роль с минимальными правами.
– Флаг или роль суперпользователя предоставляют все Права.
- Подписки — это объекты первого класса, предоставляющие дополнительные разрешения/права (например, доступ к определённому контенту фильмов). Оценка подписки может осуществляться другими сервисами с использованием токенов-заявок (например, массива `entitlements`) или через конечную точку интроспекции.

Примечания по безопасности (краткие):
- Используйте HTTPS для всего трафика.
- Храните только хеши паролей (bcrypt/argon2).
- Храните идентификаторы токенов обновления в Redis, а не необработанные токены обновления; выдавайте безопасный непрозрачный токен обновления, привязанный к этому идентификатору.
- Ротация ключей и поддержка идентификаторов ключей (kid) в заголовках JWT при использовании асимметричной подписи.

Модели Pydantic
---------------
"""

from enum import Enum
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field


class Permission(str, Enum):
    READ_PUBLIC_CONTENT = "read:public_content"
    WATCH_MOVIES = "watch:movies"
    MANAGE_USERS = "manage:users"
    MANAGE_ROLES = "manage:roles"
    MANAGE_SUBSCRIPTIONS = "manage:subscriptions"
    VIEW_ADMIN_PANEL = "view:admin_panel"


class RoleType(str, Enum):
    DEFAULT = "default"
    ADMIN = "admin"
    SYSTEM = "system"


class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expiration


class TokenPayload(BaseModel):
    sub: str  # subject: user id (UUID or DB id represented as string)
    exp: int
    iat: int
    jti: Optional[str] = None
    scopes: Optional[list[str]] = []
    roles: Optional[list[str]] = []
    entitlements: Optional[list[str]] = []


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserRead(UserBase):
    id: UUID
    roles: list[str] = []
    subscriptions: list[str] = []  # subscription ids or names
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class PasswordChange(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


class UserTokenInfo(BaseModel):
    sub: str
    email: EmailStr
    roles: list[str] = []
    entitlements: list[str] = []
    is_superuser: bool = False


class LoginRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None
    access_jti: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: str = ""  # set[Permission] = set()
    type: RoleType = RoleType.DEFAULT


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    description: Optional[str] = None
    permissions: Optional[set[Permission]] = None
    type: Optional[RoleType] = None


class RoleRead(RoleBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None


class RoleApplyRequest(BaseModel):
    user_id: UUID
    role_id: UUID
    expires_at: Optional[datetime] = None  # temporary role assignment


class RoleAssignmentRead(BaseModel):
    id: UUID
    role_id: UUID
    user_id: UUID
    assigned_by: Optional[UUID] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class SubscriptionBase(BaseModel):
    name: str
    description: Optional[str] = None
    # entitlements optionally granted by this subscription (e.g. "hd-stream", "catalog-premium")
    entitlements: set[str] = set()
    duration_days: Optional[int] = (
        None  # if recurring, this may be null/managed externally
    )


class SubscriptionCreate(SubscriptionBase):
    price_cents: Optional[int] = None


class SubscriptionRead(SubscriptionBase):
    id: UUID
    status: SubscriptionStatus
    user_id: UUID
    started_at: datetime
    ends_at: Optional[datetime] = None


class RightsCheckRequest(BaseModel):
    user_id: Optional[UUID] = None
    token: Optional[str] = None
    required_permissions: Optional[set[Permission]] = None
    required_entitlements: Optional[set[str]] = None


class RightsCheckResponse(BaseModel):
    allowed: bool
    missing_permissions: list[Permission] = []
    missing_entitlements: list[str] = []
    reason: Optional[str] = None


class PagedMeta(BaseModel):
    total: int
    page: int
    size: int


class PagedResponse(BaseModel):
    meta: PagedMeta
    items: list[BaseModel]


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class SubscriptionAssign(BaseModel):
    user_id: int
    subscription_type: str


def make_access_token_payload(
    user_id: str,
    roles: list[str],
    entitlements: list[str],
    expires_delta_seconds: int,
    jti: Optional[str] = None,
) -> TokenPayload:
    now = datetime.now()
    iat = int(now.timestamp())
    exp = int((now + timedelta(seconds=expires_delta_seconds)).timestamp())
    return TokenPayload(
        sub=user_id,
        iat=iat,
        exp=exp,
        jti=jti or str(uuid4()),
        roles=roles,
        scopes=[],
        entitlements=entitlements,
    )


class StandardResponse(BaseModel):
    detail: str


class UserRoleInput(BaseModel):
    role_id: UUID
    user_id: UUID


class LoginHistoryRead(BaseModel):
    id: UUID
    timestamp: datetime
    ip_address: str | None
    user_agent: str | None

    class Config:
        from_attributes = True
