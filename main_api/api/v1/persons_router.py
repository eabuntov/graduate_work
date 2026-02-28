from fastapi import APIRouter, Depends, HTTPException, Query
from elasticsearch import AsyncElasticsearch, NotFoundError
from typing import List, Optional

from config.config import settings
from models.models import Person
from repositories.elastic_repository import ElasticRepository
from services.person_service import PersonService

from dependencies.auth import get_current_user

persons_router = APIRouter(prefix="/persons", tags=["persons"], dependencies=[Depends(get_current_user)])


async def get_elastic_client() -> AsyncElasticsearch:
    client = AsyncElasticsearch(hosts=[settings.elk_url], verify_certs=False)
    try:
        yield client
    finally:
        await client.close()


def get_person_service(
    es: AsyncElasticsearch = Depends(get_elastic_client),
) -> PersonService:
    repo = ElasticRepository(es, index="persons", model=Person)
    return PersonService(repo)


@persons_router.get("/{person_id}", response_model=Person)
async def get_person(
    person_id: str, service: PersonService = Depends(get_person_service)
):
    """Get a single person by ID."""
    try:
        return await service.get_person(person_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Person not found")


@persons_router.get("/", response_model=List[Person])
async def list_people(
    sort: Optional[str] = Query(None),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: PersonService = Depends(get_person_service),
):
    """List or search people."""
    return await service.list_people(sort, sort_order, limit, offset)
