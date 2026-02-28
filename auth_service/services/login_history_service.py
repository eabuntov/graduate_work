from sqlalchemy import UUID

from repositories.login_history_repository import LoginHistoryRepository


class LoginHistoryService:
    def __init__(self, repo: LoginHistoryRepository):
        self.repo = repo

    async def record_login(self, user_id: UUID, ip: str | None, agent: str | None):
        return await self.repo.create(user_id=user_id, ip_address=ip, user_agent=agent)

    async def get_user_history(self, user_id: UUID, limit: int, offset: int):
        return await self.repo.get_by_user(user_id=user_id, limit=limit, offset=offset)
