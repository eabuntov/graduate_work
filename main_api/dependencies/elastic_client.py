from config.config import settings
from elasticsearch import AsyncElasticsearch, NotFoundError

async def get_elastic_client() -> AsyncElasticsearch:
    """Dependency that provides a single Elasticsearch client."""
    client = AsyncElasticsearch(hosts=[settings.elk_url], verify_certs=False)
    try:
        yield client
    finally:
        await client.close()