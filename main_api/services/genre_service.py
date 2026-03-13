import logging
from typing import Optional
from api.v1.caching import get_from_cache
from models.models import Genre
from repositories.elastic_repository import ElasticRepository

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
        self, sort: Optional[str], sort_order: str, limit: int, offset: int
    ) -> list[Genre]:
        cache_key = f"genres:list:{sort}:{sort_order}:{limit}:{offset}"
        cached = await get_from_cache(cache_key)
        if cached:
            return [Genre(**doc) for doc in cached]

        must = []

        body = {
            "query": {"bool": {"must": must or [{"match_all": {}}]}},
            "from": offset,
            "size": limit,
        }

        if sort:
            body["sort"] = [{sort: {"order": sort_order}}]

        logger.info("Executing genre search query.")
        return await self.repo.search(body)
