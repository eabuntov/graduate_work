import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from uuid import UUID

from db import get_db
from models import WatchSession, WatchSessionParticipant, CreateWatchSessionRequest
from ws_manager import SessionManager

ws_router = APIRouter()
manager = SessionManager()

templates = Jinja2Templates(directory="templates")

# Replace with your actual auth mechanism
async def get_current_user_id(websocket: WebSocket) -> str:
    token = websocket.headers.get("authorization")
    if not token:
        raise HTTPException(status_code=401)
    # validate token...
    return "mock-user-id"


@ws_router.websocket("/ws/watch/{session_id}")
async def watch_session_ws(
    websocket: WebSocket,
    session_id: str,
    db: Session = Depends(get_db),
):
    user_id = await get_current_user_id(websocket)

    # Validate session exists
    session: WatchSession = (
        db.query(WatchSession)
        .filter(WatchSession.id == UUID(session_id))
        .first()
    )

    if not session or session.status != "active":
        await websocket.close(code=4004)
        return

    # Validate participant
    participant = (
        db.query(WatchSessionParticipant)
        .filter(
            WatchSessionParticipant.session_id == UUID(session_id),
            WatchSessionParticipant.user_id == user_id,
        )
        .first()
    )

    if not participant:
        await websocket.close(code=4003)
        return

    await manager.connect(session_id, websocket)

    try:
        # 🔹 Send authoritative state immediately
        await websocket.send_json({
            "type": "sync",
            "position": session.current_position,
            "is_playing": session.is_playing,
            "server_time": time.time(),
        })

        while True:
            data = await websocket.receive_json()

            message_type = data.get("type")

            # -------------------------
            # PLAY
            # -------------------------
            if message_type == "play":
                session.current_position = float(data["position"])
                session.is_playing = True
                db.commit()

                await manager.broadcast(session_id, {
                    "type": "sync",
                    "position": session.current_position,
                    "is_playing": True,
                    "server_time": time.time(),
                })

            # -------------------------
            # PAUSE
            # -------------------------
            elif message_type == "pause":
                session.current_position = float(data["position"])
                session.is_playing = False
                db.commit()

                await manager.broadcast(session_id, {
                    "type": "sync",
                    "position": session.current_position,
                    "is_playing": False,
                    "server_time": time.time(),
                })

            # -------------------------
            # SEEK
            # -------------------------
            elif message_type == "seek":
                session.current_position = float(data["position"])
                db.commit()

                await manager.broadcast(session_id, {
                    "type": "sync",
                    "position": session.current_position,
                    "is_playing": session.is_playing,
                    "server_time": time.time(),
                })

            # -------------------------
            # CHAT
            # -------------------------
            elif message_type == "chat":
                message = data.get("message", "")

                await manager.broadcast(session_id, {
                    "type": "chat",
                    "user_id": user_id,
                    "message": message,
                    "timestamp": time.time(),
                })

    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)


@ws_router.post("/watch-sessions")
def create_watch_session(
    payload: CreateWatchSessionRequest,
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()

    # Validate movie exists
    movie = (
        db.query(FilmWork)
        .filter(FilmWork.id == UUID(payload.movie_id))
        .first()
    )

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Create session
    session = WatchSession(
        id=uuid4(),
        movie_id=movie.id,
        host_user_id=user_id,
        status="active",
        current_position=0.0,
        is_playing=False,
    )

    db.add(session)

    # Add creator as participant
    participant = WatchSessionParticipant(
        session_id=session.id,
        user_id=user_id,
    )

    db.add(participant)

    db.commit()

    return {
        "session_id": str(session.id)
    }
