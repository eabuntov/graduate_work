import json
from abc import ABC, abstractmethod
from datetime import datetime
from redis import Redis
from typing import Any, Optional

from config.config import settings


class BaseStorage(ABC):
    """Abstract base class for saving and retrieving ETL state."""

    @abstractmethod
    def save_state(self, key: str, value: Any) -> None:
        """Save a state value by key."""
        pass

    @abstractmethod
    def retrieve_state(self, key: str) -> Optional[Any]:
        """Retrieve a previously saved value by key."""
        pass


class RedisStorage(BaseStorage):
    """Redis-backed implementation of state storage."""

    def __init__(self, redis_adapter: Redis = None, namespace: str = "etl_state:"):
        self.redis_adapter = redis_adapter or Redis(
            host=settings.redis_host,
            port=int(settings.redis_port),
            db=0,
            decode_responses=True,
        )
        self.namespace = namespace

    def _full_key(self, key: str) -> str:
        return f"{self.namespace}{key}"

    def save_state(self, key: str, value: Any) -> None:
        """охраняем состояние в виде даты или JSON-строки"""
        self.redis_adapter.set(self._full_key(key), StateSerializer.serialize(value))

    def retrieve_state(self, key: str) -> Optional[str | dict]:
        """Получение состояния."""
        data = self.redis_adapter.get(self._full_key(key))
        return StateSerializer.deserialize(data)


class StateSerializer:
    @staticmethod
    def serialize(value: Any) -> str:
        if isinstance(value, datetime):
            return value.isoformat()
        return json.dumps(value)

    @staticmethod
    def deserialize(data: str) -> Any:
        if data is None:
            return None
        try:
            return datetime.fromisoformat(data)
        except ValueError:
            return json.loads(data)
