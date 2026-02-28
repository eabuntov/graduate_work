from fastapi import APIRouter, Depends, HTTPException, Query
from elasticsearch import AsyncElasticsearch, NotFoundError
from typing import List, Optional
from models.models import FilmWork
from repositories.elastic_repository import ElasticRepository
from services.film_service import FilmService

from config.config import settings
from dependencies.auth import get_current_user

films_router = APIRouter(prefix="/films", tags=["films"], dependencies=[Depends(get_current_user)],)


async def get_elastic_client() -> AsyncElasticsearch:
    """Dependency that provides a single Elasticsearch client."""
    client = AsyncElasticsearch(hosts=[settings.elk_url], verify_certs=False)
    try:
        yield client
    finally:
        await client.close()


def get_film_service(
    es: AsyncElasticsearch = Depends(get_elastic_client),
) -> FilmService:
    repo = ElasticRepository(es, index="movies", model=FilmWork)
    return FilmService(repo)


@films_router.get("/{film_id}", response_model=FilmWork)
async def get_film(film_id: str, service: FilmService = Depends(get_film_service)):
    """Get a single film by ID."""
    try:
        return await service.get_film(film_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="film not found")


@films_router.get("/", response_model=List[FilmWork])
async def list_films(
    sort: Optional[str] = Query(None),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    min_rating: Optional[float] = Query(None),
    max_rating: Optional[float] = Query(None),
    type: Optional[str] = Query(None, alias="type"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: FilmService = Depends(get_film_service),
):
    return await service.list_films(
        sort, sort_order, min_rating, max_rating, type, limit, offset
    )
