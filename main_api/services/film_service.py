import logging
from typing import Optional
from api.v1.caching import get_from_cache
from models.models import FilmWork
from repositories.elastic_repository import ElasticRepository

from dependencies.pagination import LimitOffsetParams

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
        pagination: LimitOffsetParams = None
    ) -> list[FilmWork]:
        if not pagination:
            pagination = LimitOffsetParams()
        cache_key = f"films:list:{sort}:{sort_order}:{min_rating}:{max_rating}:{type_}:{pagination.limit}:{pagination.offset}"
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
            "from": pagination.offset,
            "size": pagination.limit,
        }

        if sort:
            body["sort"] = [{sort: {"order": sort_order}}]

        logger.info("Executing film search query.")
        return await self.repo.search(body)

    async def search_films(
            self,
            query: str,
            pagination: LimitOffsetParams = None
    ) -> list[FilmWork]:
        """Full-text search for films by title or description."""
        if not pagination:
            pagination = LimitOffsetParams()
        cache_key = f"films:search:{query}:{pagination.limit}:{pagination.offset}"
        cached = await get_from_cache(cache_key)
        if cached:
            return [FilmWork(**doc) for doc in cached]

        body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "title",
                        "description",
                        "genres",
                        "directors_names",
                        "poster_url",
                    ],
                    "fuzziness": "auto",
                }
            },
            "from": pagination.offset,
            "size": pagination.limit,
        }

        logger.info(
            f"Searching films: query='{query}', offset={pagination.offset}, limit={pagination.limit}"
        )

        result = await self.repo.search(body)

        return [FilmWork(**doc) for doc in result]
