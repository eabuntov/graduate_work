import logging
from typing import Optional
from api.v1.caching import get_from_cache
from models.models import Person
from repositories.elastic_repository import ElasticRepository

logger = logging.getLogger(__name__)


class PersonService:
    """Service handling person search and retrieval."""

    def __init__(self, repo: ElasticRepository):
        self.repo = repo

    async def get_person(self, person_id: str) -> Person:
        cache_key = f"person:{person_id}"
        cached = await get_from_cache(cache_key)
        if cached:
            return Person(**cached)
        return await self.repo.get_by_id(person_id)

    async def list_people(
        self, sort: Optional[str], sort_order: str, limit: int, offset: int
    ) -> list[Person]:
        cache_key = f"people:list:{sort}:{sort_order}:{limit}:{offset}"
        cached = await get_from_cache(cache_key)
        if cached:
            return [Person(**doc) for doc in cached]

        must = []

        body = {
            "query": {"bool": {"must": must or [{"match_all": {}}]}},
            "from": offset,
            "size": limit,
        }

        if sort:
            body["sort"] = [{sort: {"order": sort_order}}]

        logger.info("Executing person search query.")
        return await self.repo.search(body)
