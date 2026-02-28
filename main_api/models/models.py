from pydantic import BaseModel, Field
from typing import Optional
import datetime


class FilmWork(BaseModel):
    id: str  # UUID
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    creation_date: Optional[datetime.date] = None
    rating: Optional[float] = None
    type: str = Field(..., min_length=1)
    created: Optional[datetime.datetime] = None
    modified: Optional[datetime.datetime] = None


class Genre(BaseModel):
    id: str  # UUID
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    created: Optional[datetime.datetime] = None
    modified: Optional[datetime.datetime] = None


class Person(BaseModel):
    id: str  # UUID
    full_name: str = Field(..., min_length=1)
    created: Optional[datetime.datetime] = None
    modified: Optional[datetime.datetime] = None


class GenreFilmWork(BaseModel):
    id: str  # UUID
    genre_id: str  # UUID
    film_work_id: str  # UUID
    created: Optional[datetime.datetime] = None


class PersonFilmWork(BaseModel):
    id: str  # UUID
    person_id: str  # UUID
    film_work_id: str  # UUID
    role: str = Field(..., min_length=1)
    created: Optional[datetime.datetime] = None


if __name__ == "__main__":
    # Example Usage (optional)
    film = FilmWork(
        id="a1b2c3d4-e5f6-7890-1234-567890abcdef",
        title="Example Movie",
        description="This is an example movie.",
        creation_date=datetime.date(2023, 10, 26),
        rating=8.5,
        type="movie",
    )
    print(film)

    genre = Genre(
        id="f1g2h3i4-j5k6-l7m8-n9o0-p1q2r3s4t5u6",
        name="Comedy",
        description="Funny movies.",
    )
    print(genre)

    person = Person(id="v1w2x3y4-z5a6-b7c8-d9e0-f1g2h3i4j5k6", full_name="John Doe")
    print(person)

    person_film_work = PersonFilmWork(
        id="y1z2a3b4-c5d6-e7f8-g9h0-i1j2k3l4m5n6",
        person_id="v1w2x3y4-z5a6-b7c8-d9e0-f1g2h3i4j5k6",
        film_work_id="a1b2c3d4-e5f6-7890-1234-567890abcdef",
        role="actor",
    )
    print(person_film_work)
