from fastapi import APIRouter, Depends, HTTPException, Query
from elasticsearch import AsyncElasticsearch, NotFoundError
from typing import List, Optional

from config.config import settings
from models.models import Genre
from repositories.elastic_repository import ElasticRepository
from services.genre_service import GenreService
from dependencies.auth import get_current_user

genres_router = APIRouter(prefix="/genres", tags=["genres"], dependencies=[Depends(get_current_user)])


async def get_elastic_client() -> AsyncElasticsearch:
    client = AsyncElasticsearch(hosts=[settings.elk_url], verify_certs=False)
    try:
        yield client
    finally:
        await client.close()


def get_genre_service(
    es: AsyncElasticsearch = Depends(get_elastic_client),
) -> GenreService:
    repo = ElasticRepository(es, index="genres", model=Genre)
    return GenreService(repo)


@genres_router.get("/{genre_id}", response_model=Genre)
async def get_genre(genre_id: str, service: GenreService = Depends(get_genre_service)):
    """Get a single genre by ID."""
    try:
        return await service.get_genre(genre_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Genre not found")


@genres_router.get("/", response_model=List[Genre])
async def list_genres(
    sort: Optional[str] = Query(None),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: GenreService = Depends(get_genre_service),
):
    """List or search genres."""
    return await service.list_genres(sort, sort_order, limit, offset)
