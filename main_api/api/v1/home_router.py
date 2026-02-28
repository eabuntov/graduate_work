from typing import Any, AsyncGenerator, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from elasticsearch import AsyncElasticsearch

from config.config import settings
from repositories.elastic_repository import ElasticRepository
from services.film_service import FilmService
from models.models import FilmWork

from dependencies.auth import get_anonymous_user

templates = Jinja2Templates(directory="templates")

home_router = APIRouter(tags=["home"], dependencies=[Depends(get_anonymous_user)])


async def get_elastic_client() -> AsyncGenerator[AsyncElasticsearch, Any]:
    """Provides a shared Elasticsearch client for dependency injection."""
    client = AsyncElasticsearch(hosts=[settings.elk_url], verify_certs=False)
    try:
        yield client
    finally:
        await client.close()


def get_film_service(
    es: AsyncElasticsearch = Depends(get_elastic_client),
) -> FilmService:
    """Factory for filmService."""
    repo = ElasticRepository(es, index="movies", model=FilmWork)
    return FilmService(repo)


@home_router.get("/", response_class=HTMLResponse)
async def home(
    sort: Optional[str] = Query(None),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    min_rating: Optional[float] = Query(None),
    max_rating: Optional[float] = Query(None),
    type: Optional[str] = Query(None, alias="type"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: FilmService = Depends(get_film_service),
):
    films = await service.list_films(
        sort, sort_order, min_rating, max_rating, type, limit, offset
    )
    return templates.TemplateResponse(
        "index.html",
        {"request": {}, "films": films},
    )
