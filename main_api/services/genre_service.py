import logging
from typing import Optional
from api.v1.caching import get_from_cache
from models.models import Genre
from repositories.elastic_repository import ElasticRepository

from dependencies.pagination import LimitOffsetParams

logger = logging.getLogger(__name__)


class GenreService:
    """Service handling genre search and retrieval."""

    def __init__(self, repo: ElasticRepository):
        self.repo = repo

    async def get_genre(self, genre_id: str) -> Genre:
        cache_key = f"genre:{genre_id}"
        cached = await get_from_cache(cache_key)
        if cached:
            return Genre(**cached)
        return await self.repo.get_by_id(genre_id)

    async def list_genres(
        self, sort: Optional[str], sort_order: str,
            pagination: LimitOffsetParams = None
    ) -> list[Genre]:
        if not pagination:
            pagination = LimitOffsetParams()
        cache_key = f"genres:list:{sort}:{sort_order}:{pagination.limit}:{pagination.offset}"
        cached = await get_from_cache(cache_key)
        if cached:
            return [Genre(**doc) for doc in cached]

        must = []

        body = {
            "query": {"bool": {"must": must or [{"match_all": {}}]}},
            "from": pagination.offset,
            "size": pagination.limit,
        }

        if sort:
            body["sort"] = [{sort: {"order": sort_order}}]

        logger.info("Executing genre search query.")
        return await self.repo.search(body)
