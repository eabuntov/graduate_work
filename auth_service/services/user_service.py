from typing import Optional

from pydantic import EmailStr
from sqlalchemy import UUID

from models.db_models import User, Subscription
from repositories.user_repository import UserRepository
from repositories.roles_repository import RoleRepository
from security.password import PasswordHasher


class UserService:
    def __init__(
        self,
        repo: UserRepository,
        hasher: PasswordHasher,
        role_repo: RoleRepository,
        default_role_name: str = "user",
    ):
        self.repo = repo
        self.hasher = hasher
        self.role_repo = role_repo
        self.default_role_name = default_role_name

    async def register(
        self, email: EmailStr, password: str, full_name: Optional[str] = None
    ):
        existing = await self.repo.get_by_email(email)
        if existing:
            raise ValueError("Email already registered")

        password_hash = self.hasher.hash_password(password)

        # 1. Create user
        user = await self.repo.create(
            email=email,
            full_name=full_name,
            password_hash=password_hash,
        )

        # 2. Load default role
        default_role = await self.role_repo.get_by_name(self.default_role_name)
        if default_role:
            # 3. Add to user's roles
            user.roles.append(default_role)
            await self.repo.update(user)

        return user

    async def authenticate(self, email: EmailStr, password: str):
        user = await self.repo.get_by_email(email)
        if not user:
            return None

        if not self.hasher.verify_password(password, user.password_hash):
            return None

        return user

    async def change_password(self, user: User, old_password: str, new_password: str):
        if not self.hasher.verify_password(old_password, user.password_hash):
            raise ValueError("Old password incorrect")

        user.password_hash = self.hasher.hash_password(new_password)

        await self.repo.update(user)
        return user

    async def get_user_subscriptions(self, user_id: UUID) -> list[Subscription]:
        """Return all active subscriptions for the given user."""
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Assuming User.subscriptions is a relationship loaded by ORM
        return list(user.subscriptions)

    async def get_user_permissions(self, user_id: UUID) -> set[str]:
        """
        Aggregate permissions from:
            - Role.permissions    (comma-separated)
            - Subscription.entitlements  (comma-separated)
        Returns a unique list of permissions.
        """
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        permissions: set[str] = set()

        # From roles
        for role in user.roles:
            if role.permissions:
                perms = [p.strip() for p in role.permissions.split(",") if p.strip()]
                permissions.update(perms)

        # From subscriptions
        for sub in user.subscriptions:
            if sub.entitlements:
                ents = [e.strip() for e in sub.entitlements.split(",") if e.strip()]
                permissions.update(ents)

        return permissions

    async def get_or_create_oauth_user(
            self,
            provider: str,
            provider_id: str,
            email: str | None,
            full_name: str | None,
    ):
        user = await self.repo.get_by_oauth(provider, provider_id)

        if user:
            return user

        if email:
            user = await self.repo.get_by_email(email)
            if user:
                await self.repo.attach_oauth(user.id, provider, provider_id)
                return user

        return await self.repo.create_oauth_user(
            email=email,
            full_name=full_name,
            provider=provider,
            provider_id=provider_id,
        )
