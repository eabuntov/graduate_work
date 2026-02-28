from elasticsearch import AsyncElasticsearch
from typing import Any, TypeVar

T = TypeVar("T")


class ElasticRepository:
    """Generic repository for Elasticsearch operations."""

    def __init__(self, es: AsyncElasticsearch, index: str, model: type[T]):
        self.es = es
        self.index = index
        self.model = model

    async def get_by_id(self, entity_id: str) -> T:
        result = await self.es.get(index=self.index, id=entity_id)
        return self.model(**result["_source"])

    async def search(self, body: dict[str, Any]) -> list[T]:
        resp = await self.es.search(index=self.index, body=body)
        return [self.model(**hit["_source"]) for hit in resp["hits"]["hits"]]
