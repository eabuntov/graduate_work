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
    PROJECT_NAME: str = "Auth Service"
    RATE_LIMIT: int = Field(20, env="RATE_LIMIT")
    WINDOW_SECONDS: int = Field(60, env="WINDOW_SECONDS")
    SERVICE_NAME: str = Field("auth-service", env="SERVICE_NAME")
    ENVIRONMENT: str = Field("production", env="ENVIRONMENT")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    JAEGER_AGENT_HOST: str = Field("jaeger", env="JAEGER_AGENT_HOST")
    JAEGER_AGENT_PORT: str = Field("6831", env="JAEGER_AGENT_PORT")
    OTEL_TRACES_SAMPLER: str = Field("parentbased_traceidratio", env="OTEL_TRACES_SAMPLER")
    OTEL_TRACES_SAMPLER_ARG: str = Field("0.1", env="OTEL_TRACES_SAMPLER_ARG")
    OAUTH_PROVIDERS: dict = Field({
        "yandex": {
            "client_id": "YANDEX_CLIENT_ID",
            "client_secret": "YANDEX_CLIENT_SECRET",
            "authorize_url": "https://oauth.yandex.ru/authorize",
            "access_token_url": "https://oauth.yandex.ru/token",
            "userinfo_url": "https://login.yandex.ru/info",
            "scope": "login:email",
        },
        "google": {
            "client_id": "GOOGLE_CLIENT_ID",
            "client_secret": "GOOGLE_CLIENT_SECRET",
            "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "access_token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
            "scope": "openid email profile",
        },
    })

settings = Settings()
