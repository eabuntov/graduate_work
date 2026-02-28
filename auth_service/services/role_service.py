from typing import Optional

from sqlalchemy import UUID

from models.db_models import Role
from repositories.roles_repository import RoleRepository
from repositories.user_repository import UserRepository


class RoleService:
    def __init__(self, role_repo: RoleRepository, user_repo: UserRepository = None):
        self.role_repo = role_repo
        self.user_repo = user_repo

    async def create_role(
        self, name: str, permissions: str, description: Optional[str] = None
    ) -> Role:
        existing = await self.role_repo.get_by_name(name)
        if existing:
            raise ValueError("Role already exists")
        return await self.role_repo.create(
            name=name, permissions=permissions, description=description
        )

    async def list_roles(self) -> list[Role]:
        return await self.role_repo.list_all()

    async def assign_role(self, user_id: UUID, role_id: UUID):
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise ValueError("Role not found")
        if role not in user.roles:
            user.roles.append(role)
            await self.user_repo.update(user)

    async def remove_role(self, user_id: UUID, role_id: UUID):
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise ValueError("Role not found")
        if role in user.roles:
            user.roles.remove(role)
            await self.user_repo.update(user)
