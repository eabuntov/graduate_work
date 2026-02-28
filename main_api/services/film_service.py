import logging
from typing import Optional
from api.v1.caching import get_from_cache
from models.models import FilmWork
from repositories.elastic_repository import ElasticRepository

logger = logging.getLogger(__name__)


class FilmService:
    """Service handling film search and retrieval."""

    def __init__(self, repo: ElasticRepository):
        self.repo = repo

    async def get_film(self, film_id: str) -> FilmWork:
        cache_key = f"film:{film_id}"
        cached = await get_from_cache(cache_key)
        if cached:
            return FilmWork(**cached)
        return await self.repo.get_by_id(film_id)

    async def list_films(
        self,
        sort: Optional[str] = "rating",
        sort_order: str = "desc",
        min_rating: Optional[float] = 0.0,
        max_rating: Optional[float] = 10.0,
        type_: Optional[str] = "movie",
        limit: int = 10,
        offset: int = 0,
    ) -> list[FilmWork]:
        cache_key = f"films:list:{sort}:{sort_order}:{min_rating}:{max_rating}:{type_}:{limit}:{offset}"
        cached = await get_from_cache(cache_key)
        if cached:
            return [FilmWork(**doc) for doc in cached]

        must, filters = [], []

        if min_rating is not None or max_rating is not None:
            range_filter = {}
            if min_rating is not None:
                range_filter["gte"] = min_rating
            if max_rating is not None:
                range_filter["lte"] = max_rating
            filters.append({"range": {"rating": range_filter}})

        if type_:
            filters.append({"term": {"type.keyword": type_}})

        body = {
            "query": {"bool": {"must": must or [{"match_all": {}}], "filter": filters}},
            "from": offset,
            "size": limit,
        }

        if sort:
            body["sort"] = [{sort: {"order": sort_order}}]

        logger.info("Executing film search query.")
        return await self.repo.search(body)

    async def search_films(
        self, query: str, page_number: int = 1, page_size: int = 10
    ) -> list[FilmWork]:
        """Full-text search for films by title or description."""
        cache_key = f"films:search:{query}:{page_number}:{page_size}"
        cached = await get_from_cache(cache_key)
        if cached:
            return [FilmWork(**doc) for doc in cached]

        # Elasticsearch query
        body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title", "description", "genres", "directors_names"],
                    "fuzziness": "auto",
                }
            },
            "from": (page_number - 1) * page_size,
            "size": page_size,
        }

        logger.info(
            f"Searching films: query='{query}', page={page_number}, size={page_size}"
        )
        return await self.repo.search(body)
