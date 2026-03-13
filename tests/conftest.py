import sys
from uuid import uuid4

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from movies_together_api.main import app
from movies_together_api.models import WatchSessionParticipant, WatchSession, FilmWork

sys.path.append("/opt/app/src")

# -----------------------------------------------------------------------------
# Test DB Setup
# -----------------------------------------------------------------------------

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def create_test_session(db):
    movie_id = uuid4()
    session_id = uuid4()
    user_id = uuid4()

    movie = FilmWork(
        id=movie_id,
        title="Test Movie",
        video_url="http://example.com/video.mp4",
        poster_url="http://example.com/poster.jpg",
        duration_seconds=120,
    )
    db.add(movie)

    session = WatchSession(
        id=session_id,
        movie_id=movie_id,
        host_id=user_id,
        current_position=0,
        is_playing=False,
        status="active",
    )
    db.add(session)

    participant = WatchSessionParticipant(
        session_id=session_id,
        user_id=user_id,
        role="host",
    )
    db.add(participant)

    db.commit()

    return str(session_id), str(user_id)