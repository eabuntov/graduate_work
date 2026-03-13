import jwt
from datetime import datetime, timedelta
from config.settings import settings


class JWTHandler:
    def __init__(self):
        self.access_secret = settings.JWT_ACCESS_SECRET
        self.refresh_secret = settings.JWT_REFRESH_SECRET
        self.algorithm = settings.JWT_ALGORITHM
        self.access_exp = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_exp = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(
        self, user_id: int, extra_claims: dict | None = None
    ) -> str:
        payload = {
            "sub": str(user_id),
            "iat": datetime.now(),
            "exp": datetime.now() + timedelta(minutes=self.access_exp),
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(payload, self.access_secret, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "iat": datetime.now(),
            "exp": datetime.now() + timedelta(days=self.refresh_exp),
            "typ": "refresh",
        }
        return jwt.encode(payload, self.refresh_secret, algorithm=self.algorithm)

    def verify_access(self, token: str) -> dict:
        return jwt.decode(token, self.access_secret, algorithms=[self.algorithm])

    def verify_refresh(self, token: str) -> dict:
        payload = jwt.decode(token, self.refresh_secret, algorithms=[self.algorithm])
        if payload.get("typ") != "refresh":
            raise jwt.InvalidTokenError("Not a refresh token")
        return payload

    def decode(self, token: str, refresh: bool = False) -> dict:
        secret = self.refresh_secret if refresh else self.access_secret
        return jwt.decode(token, secret, algorithms=[self.algorithm])
