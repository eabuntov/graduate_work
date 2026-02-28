from fastapi import APIRouter, Depends, Query
from elasticsearch import AsyncElasticsearch
from typing import Any, AsyncGenerator

from config.config import settings
from models.models import FilmWork
from repositories.elastic_repository import ElasticRepository
from services.film_service import FilmService

from dependencies.auth import get_current_user

films_search_router = APIRouter(prefix="/search", tags=["search"], dependencies=[Depends(get_current_user)])


# --- Dependencies ---
async def get_elastic_client() -> AsyncGenerator[AsyncElasticsearch, Any]:
    """Provide a single Elasticsearch client per request."""
    client = AsyncElasticsearch(hosts=[settings.elk_url], verify_certs=False)
    try:
        yield client
    finally:
        await client.close()


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
    page_number: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Results per page"),
    service: FilmService = Depends(get_film_service),
):
    """
    Search films by title or description.
    Returns paginated FilmWork results.
    """
    return await service.search_films(
        query=query, page_number=page_number, page_size=page_size
    )
