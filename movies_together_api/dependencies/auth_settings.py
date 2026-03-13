from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(extra="allow", env_file=".env")
    # ---------------------- JWT ----------------------
    JWT_ACCESS_SECRET: str = Field(..., env="JWT_ACCESS_SECRET")
    JWT_REFRESH_SECRET: str = Field(..., env="JWT_REFRESH_SECRET")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(15, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(30, env="REFRESH_TOKEN_EXPIRE_DAYS")

    # ---------------------- PASSWORD HASHING ----------------------
    BCRYPT_ROUNDS: int = Field(12, env="BCRYPT_ROUNDS")

    # ---------------------- APP SETTINGS ----------------------
    DEBUG: bool = Field(False, env="DEBUG")

    REDIS_URL: str = Field(..., env="REDIS-HOST")
    DATABASE_URL: str = Field(..., env="AUTH_DATABASE_URL")
    AUTH_ISSUER: str = "auth-app"


settings = Settings()
