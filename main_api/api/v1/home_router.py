from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from elasticsearch import AsyncElasticsearch

from repositories.elastic_repository import ElasticRepository
from services.film_service import FilmService
from models.models import FilmWork

from dependencies.auth import require_user

from dependencies.elastic_client import get_elastic_client

templates = Jinja2Templates(directory="templates")

home_router = APIRouter(tags=["home"], dependencies=[Depends(require_user)])


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

@home_router.get("/movies/{movie_id}", response_class=HTMLResponse)
async def get_movie_page(
    request: Request,
    movie_id: str,
    service: FilmService = Depends(get_film_service),
):
    film = await service.get_film(movie_id)

    if not film:
        raise HTTPException(status_code=404, detail="Movie not found")

    return templates.TemplateResponse(
        "movie.html",
        {
            "request": request,
            "film": film,
            "movie_id": movie_id
        }
    )
