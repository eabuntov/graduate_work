from typing import Any


class MovieTransformer:
    ROLE_MAP = {"director": "directors", "actor": "actors", "writer": "writers"}

    def transform(self, row: dict[str, Any]) -> dict[str, Any]:
        persons = row.get("persons") or []
        grouped = {v: [] for v in self.ROLE_MAP.values()}
        for p in persons:
            role = p.get("role")
            if role in self.ROLE_MAP:
                grouped[self.ROLE_MAP[role]].append(
                    {"id": str(p["id"]), "name": p["name"]}
                )

        return {
            "id": str(row["id"]),
            "rating": float(row["rating"]) if row["rating"] else None,
            "genres": row.get("genres", []),
            "title": row["title"],
            "type": row["type"],
            "description": row["description"],
            "directors_names": [p["name"] for p in grouped["directors"]],
            "actors_names": [p["name"] for p in grouped["actors"]],
            "writers_names": [p["name"] for p in grouped["writers"]],
            "directors": grouped["directors"],
            "actors": grouped["actors"],
            "writers": grouped["writers"],
        }


class GenreTransformer:
    def transform(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(row["id"]),
            "name": row.get("name"),
            "description": row.get("description"),
            "created": row.get("created"),
            "modified": row.get("modified"),
        }


class PersonTransformer:
    def transform(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(row["id"]),
            "full_name": row.get("full_name"),
            "created": row.get("created"),
            "modified": row.get("modified"),
        }


class TransformerFactory:
    _registry = {
        "movie": MovieTransformer(),
        "genre": GenreTransformer(),
        "person": PersonTransformer(),
    }

    @classmethod
    def get(cls, type_: str):
        return cls._registry[type_]
