from fastapi import APIRouter, Depends, Query
from elasticsearch import AsyncElasticsearch
from models.models import FilmWork
from repositories.elastic_repository import ElasticRepository
from services.film_service import FilmService

from dependencies.auth import require_user

from dependencies.elastic_client import get_elastic_client

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
    query: str = Query(..., description="Search query string"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: FilmService = Depends(get_film_service),
):
    """
    Search films by title or description.
    Returns paginated FilmWork results.
    """
    return await service.search_films(
        query=query, limit=limit, page_size=offset
    )
