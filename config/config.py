import logging
import logging.config
import sys
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def setup_logging(log_level: str = logging.INFO) -> None:
    """Configure logging for the ETL worker."""
    log_dir = Path("/opt/app/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d) [trace_id=%(trace_id)s]: %(message)s"
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "standard",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str("/opt/app/app.log"),
                "maxBytes": 5 * 1024 * 1024,  # 5 MB
                "backupCount": 3,
                "encoding": "utf-8",
                "formatter": "detailed",
            },
        },
        "root": {
            "handlers": ["console", "file"],  # both console + file
            "level": log_level,
        },
    }

    logging.config.dictConfig(logging_config)
    logging.getLogger(__name__).info("Logging initialized")


class Settings(BaseSettings):
    def __init__(self, **values: Any):
        super().__init__(**values)
        setup_logging()

    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8")

    # Database settings
    db_user: str = Field(..., alias="DB_USER")
    db_password: str = Field(..., alias="DB_PASSWORD")
    db_name: str = Field(..., alias="DB_NAME")
    db_host: str = Field(..., alias="DB_HOST")
    db_port: int = Field(5432, alias="DB_PORT")
    sql_options: str = Field("-c search_path=public,content", alias="SQL_OPTIONS")
    database_type: str = Field("postgres", alias="DATABASE_TYPE")
    batch_size: int = Field(1000, alias="BATCH_SIZE")

    # Elasticsearch settings
    elk_url: str = Field(..., alias="ELK_URL")
    elk_index: str = Field(..., alias="ELK_INDEX")
    elk_port: int = Field(9200, alias="ELK_PORT")

    # Other settings
    schema_file: str = Field(..., alias="SCHEMA_FILE")

    # Redis settings
    redis_host: str = Field(..., alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")


settings = Settings()
