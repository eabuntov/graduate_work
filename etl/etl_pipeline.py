import logging
import sys

sys.path.append("/opt")
from config.config import settings
from es_loader import ElasticLoader
from state_storage import RedisStorage
from pg_extractor import PostgresExtractor
from pg_listener import PostgresListener
from etl_transformer import TransformerFactory


class EntityETL:
    def __init__(
        self, name: str, extractor, fetch_fn, transformer, loader, state, index: str
    ):
        self.name = name
        self.extractor = extractor
        self.fetch_fn = fetch_fn
        self.transformer = transformer
        self.loader = loader
        self.state = state
        self.index = index

    def run(self, batch_size: int):
        logging.info(f"Starting {self.name} ETL...")
        time = self.state.retrieve_state(f"{self.name}_time")
        ids = self.state.retrieve_state(f"{self.name}_ids")
        for rows in self.fetch_fn(time, ids, batch_size=batch_size):
            transformed = [self.transformer.transform(r) for r in rows]
            self.loader.load_bulk(transformed, index=self.index)
            if rows:
                self.state.save_state(
                    f"{self.name}_time",
                    rows[-1].get("updated") or rows[-1].get("created"),
                )
                self.state.save_state(
                    f"{self.name}_ids", [r["id"] for r in transformed]
                )
            logging.info(
                f"Loaded {len(transformed)} {self.name} records into Elasticsearch"
            )


class ETLPipeline:
    def __init__(self, extractor, loader, state):
        self.entities = [
            EntityETL(
                "movies",
                extractor,
                extractor.fetch_movies,
                TransformerFactory.get("movie"),
                loader,
                state,
                "movies",
            ),
            EntityETL(
                "genres",
                extractor,
                extractor.fetch_genres,
                TransformerFactory.get("genre"),
                loader,
                state,
                "genres",
            ),
            EntityETL(
                "persons",
                extractor,
                extractor.fetch_people,
                TransformerFactory.get("person"),
                loader,
                state,
                "persons",
            ),
        ]

    def run(self, batch_size: int):
        for etl in self.entities:
            etl.run(batch_size)


def main():
    postgres_dsl = {
        "dbname": settings.db_name,
        "user": settings.db_user,
        "password": settings.db_password,
        "host": settings.db_host,
        "port": settings.db_port,
    }
    extractor = PostgresExtractor(postgres_dsl)
    loader = ElasticLoader()
    state = RedisStorage()
    pipeline = ETLPipeline(extractor, loader, state)
    pipeline.run(batch_size=int(settings.batch_size))

    listener = PostgresListener(postgres_dsl)
    for change in listener.wait_for_changes():
        listener.handle_change(change)


if __name__ == "__main__":
    main()
