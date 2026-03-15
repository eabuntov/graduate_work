from fastapi import APIRouter, Depends, Query
from elasticsearch import AsyncElasticsearch
from models.models import FilmWork
from repositories.elastic_repository import ElasticRepository
from services.film_service import FilmService
from typing import Annotated

from dependencies.auth import require_user

from dependencies.elastic_client import get_elastic_client

from dependencies.pagination import LimitOffsetParams

films_search_router = APIRouter(prefix="/search", tags=["search"], dependencies=[Depends(require_user)])


def get_film_service(
    es: AsyncElasticsearch = Depends(get_elastic_client),
) -> FilmService:
    """Build FilmService with an Elasticsearch repository."""
    repo = ElasticRepository(es, index="movies", model=FilmWork)
    return FilmService(repo)


# --- Endpoint ---
@films_search_router.get("/", response_model=list[FilmWork])
async def search_films(
    pagination: Annotated[LimitOffsetParams, Depends(LimitOffsetParams)],
    query: str = Query(..., description="Search query string"),
    service: FilmService = Depends(get_film_service),
):
    """
    Search films by title or description.
    Returns paginated FilmWork results.
    """
    return await service.search_films(
        query=query, pagination=pagination
    )
