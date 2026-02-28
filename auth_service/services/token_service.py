from typing import Optional

from config.settings import settings
from models.db_models import User
from security.jwt_routines import JWTHandler


class TokenService:
    def __init__(self, jwt_handler: Optional[JWTHandler] = None):
        self.jwt = jwt_handler or JWTHandler()
        self.refresh_expire_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    def create_access_token(
        self,
        user: User,
        roles: list[str],
        entitlements: list[str],
    ) -> str:
        extra_claims = {
            "email": user.email,
            "roles": roles,
            "entitlements": entitlements,
        }
        return self.jwt.create_access_token(user_id=user.id, extra_claims=extra_claims)

    def create_refresh_token(self, user: User) -> str:
        return self.jwt.create_refresh_token(user_id=user.id)

    def create_token_pair(
        self,
        user: User,
        roles: list[str],
        entitlements: list[str],
    ) -> dict:
        """
        Returns {"access_token": ..., "refresh_token": ...}
        """
        access = self.create_access_token(user, roles, entitlements)
        refresh = self.create_refresh_token(user)
        return {"access_token": access, "refresh_token": refresh}

    # ---------------------- VERIFY / DECODE ----------------------
    def decode_access(self, token: str) -> dict:
        return self.jwt.verify_access(token)

    def decode_refresh(self, token: str) -> dict:
        return self.jwt.verify_refresh(token)

    def decode_any(self, token: str) -> dict:
        """
        Automatically tries access first, then refresh.
        """
        try:
            return self.jwt.verify_access(token)
        except Exception:
            return self.jwt.verify_refresh(token)
