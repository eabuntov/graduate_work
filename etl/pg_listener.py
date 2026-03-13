import json
import logging
from typing import Any, Generator

import select

from db_routines import connect_and_listen, get_db_cursor


class PostgresListener:
    """LISTEN/NOTIFY слушатель с автопереподключением"""

    def __init__(self, dsn: dict[str, Any], channel: str = "content_changes"):
        self.dsn = dsn
        self.channel = channel
        self.conn, self.cur = connect_and_listen(dsn, channel)

    def wait_for_changes(
        self, timeout: int = 5
    ) -> Generator[dict[str, Any], None, None]:
        """Ожидание событий"""
        logging.info(f"Listening for changes on '{self.channel}'...")

        while True:
            try:
                # Check connection state
                if not self.conn or self.conn.closed:
                    self.conn, self.cur = connect_and_listen(self.dsn, self.channel)

                if select.select([self.conn], [], [], timeout) == ([], [], []):
                    continue

                self.conn.poll()

                while self.conn.notifies:
                    notify = self.conn.notifies.pop(0)
                    yield json.loads(notify.payload)
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON payload received: {e}")

    def handle_change(self, payload: dict):
        table = payload["table"]
        op = payload["operation"]
        row_id = payload["id"]

        if table != "film_work":
            # if a related table changes, reload film_work too
            self.refresh_related_films(row_id, table)
            return

        if op == "DELETE":
            self.es.delete(index=self.index, id=row_id, ignore=[404])
            logging.info(f"Deleted film {row_id} from Elasticsearch")
        else:
            row = self.fetch_film(row_id)
            if row:
                doc = self.transformer.transform(dict(row))
                self.es.index(index=self.index, id=row_id, document=doc)
                logging.debug(f"Upserted film {row_id} into Elasticsearch")

    def refresh_related_films(self, row_id: str, table: str):
        """When person/genre links change, reload affected film(s)."""
        query = None
        if table == "genre":
            query = """SELECT DISTINCT gfw.film_work_id
                       FROM content.genre_film_work gfw WHERE gfw.genre_id = %s"""
        elif table == "person":
            query = """SELECT DISTINCT pfw.film_work_id
                       FROM content.person_film_work pfw WHERE pfw.person_id = %s"""
        elif table in ("genre_film_work", "person_film_work"):
            query = f"SELECT film_work_id FROM content.{table} WHERE id = %s"

        if not query:
            return

        with get_db_cursor(self.dsn) as cur:
            cur.execute(query, (row_id,))
            film_ids = [r[0] for r in cur.fetchall()]

        for film_id in film_ids:
            row = self.fetch_film(film_id)
            if row:
                doc = self.transformer.transform(dict(row))
                self.es.update(index=self.index, id=film_id, document=doc)
                logging.debug(f"Refreshed film {film_id} due to {table} change")
