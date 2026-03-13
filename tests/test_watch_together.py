import pytest
from http import HTTPStatus
from uuid import uuid4

from fastapi.testclient import TestClient

from main import app
from db import Base, engine, SessionLocal
from models import WatchSession, WatchSessionParticipant, Movie

from tests.conftest import create_test_session


# -----------------------------------------------------------------------------
# HTTP Router Tests
# -----------------------------------------------------------------------------

def test_watch_page_returns_html(client, db):
    """Check that /watch/{session_id} returns HTML page."""

    session_id, _ = create_test_session(db)

    resp = client.get(f"/watch/{session_id}")

    assert resp.status_code == HTTPStatus.OK
    assert "text/html" in resp.headers["content-type"]
    assert "Test Movie" in resp.text


def test_watch_page_not_found(client):
    """Invalid session should return 404."""

    resp = client.get(f"/watch/{uuid4()}")

    assert resp.status_code == HTTPStatus.NOT_FOUND


# -----------------------------------------------------------------------------
# WebSocket Router Tests
# -----------------------------------------------------------------------------

def test_websocket_connect_and_receive_sync(client, db):
    """Client connects and receives initial sync state."""

    session_id, user_id = create_test_session(db)

    with client.websocket_connect(
        f"/ws/watch/{session_id}",
        headers={"authorization": "test-token"},
    ) as websocket:

        data = websocket.receive_json()

        assert data["type"] == "sync"
        assert "position" in data
        assert "is_playing" in data
        assert "server_time" in data


def test_websocket_play_event_broadcast(client, db):
    """Sending play event should return updated sync."""

    session_id, user_id = create_test_session(db)

    with client.websocket_connect(
        f"/ws/watch/{session_id}",
        headers={"authorization": "test-token"},
    ) as websocket:

        websocket.receive_json()  # initial sync

        websocket.send_json({
            "type": "play",
            "position": 10.0,
        })

        data = websocket.receive_json()

        assert data["type"] == "sync"
        assert data["is_playing"] is True
        assert data["position"] == 10.0


def test_websocket_chat_event(client, db):
    """Chat message should be broadcast."""

    session_id, user_id = create_test_session(db)

    with client.websocket_connect(
        f"/ws/watch/{session_id}",
        headers={"authorization": "test-token"},
    ) as websocket:

        websocket.receive_json()  # initial sync

        websocket.send_json({
            "type": "chat",
            "message": "Hello world",
        })

        data = websocket.receive_json()

        assert data["type"] == "chat"
        assert data["message"] == "Hello world"
        assert "timestamp" in data