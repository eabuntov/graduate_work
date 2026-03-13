import logging
import time
import requests
from typing import Any, Protocol, Optional, Callable
from elasticsearch import Elasticsearch, helpers
from config.config import settings
from apply_es_schemas import apply_elastic_schemas


class HealthChecker(Protocol):
    def wait_until_ready(self) -> None: ...


class SchemaApplier(Protocol):
    def apply(self) -> None: ...


class ElasticsearchHealthChecker:
    """Waits until Elasticsearch cluster reaches yellow or green state."""

    def __init__(self, url: str = settings.elk_url):
        self.url = url

    def wait_until_ready(self) -> None:
        logging.info("⏳ Waiting for Elasticsearch...")
        while True:
            try:
                r = requests.get(
                    f"{self.url}/_cluster/health",
                    params={"wait_for_status": "yellow", "timeout": "1s"},
                )
                if r.ok and r.json().get("status") in ("yellow", "green"):
                    logging.info("✅ Elasticsearch is ready.")
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)


class ElasticsearchSchemaApplier:
    """Applies predefined Elasticsearch schemas."""

    def __init__(self, apply_func: Callable = apply_elastic_schemas):
        self.apply_func = apply_func

    def apply(self) -> None:
        self.apply_func()


class ElasticLoader:
    """Handles loading, updating, and deleting data in Elasticsearch."""

    def __init__(
        self,
        es_client: Optional[Elasticsearch] = None,
        health_checker: Optional[HealthChecker] = ElasticsearchHealthChecker(),
        schema_applier: Optional[SchemaApplier] = ElasticsearchSchemaApplier(),
        es_host: str = settings.elk_url,
    ):
        if health_checker:
            health_checker.wait_until_ready()
        self.es = es_client or Elasticsearch([es_host])
        if schema_applier:
            schema_applier.apply()

    def load_bulk(self, docs: list[dict[str, Any]], index: str) -> None:
        """Insert or replace multiple documents."""
        logging.info(f"📦 Loading {len(docs)} documents into {index}...")
        actions = [
            {"_op_type": "index", "_index": index, "_id": doc["id"], "_source": doc}
            for doc in docs
        ]
        helpers.bulk(self.es, actions)
        logging.info(f"✅ Loaded {len(actions)} documents into {index}.")

    def update(self, index: str, doc_id: str, doc: dict[str, Any]) -> None:
        """Partial update of a document."""
        logging.info(f"🧩 Updating document {doc_id} in {index}...")
        self.es.update(index=index, id=doc_id, doc={"doc": doc})

    def delete(self, index: str, doc_id: str) -> None:
        """Deletes a document by ID."""
        logging.info(f"🗑️ Deleting document {doc_id} from {index}...")
        self.es.delete(index=index, id=doc_id)
