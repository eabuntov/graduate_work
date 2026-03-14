import logging
import time
from uuid import UUID, uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dependencies.auth import require_user, require_user_ws
from db import get_db
from db import get_db
from models import WatchSession, WatchSessionParticipant, CreateWatchSessionRequest, FilmWork
from ws_manager import SessionManager


ws_router = APIRouter(prefix="/ws")
manager = SessionManager()

templates = Jinja2Templates(directory="templates")


# -----------------------------------------------------------------------------
# Mock Auth
# -----------------------------------------------------------------------------

async def get_current_user_id(websocket: WebSocket) -> str:
    token = websocket.headers.get("authorization")
    if not token:
        raise HTTPException(status_code=401)
    return "10a6e3d6-71ba-427d-9f05-e0409a207b06"



# -----------------------------------------------------------------------------
# WebSocket Watch Session
# -----------------------------------------------------------------------------

@ws_router.websocket("/watch/{session_id}")
async def watch_session_ws(
    websocket: WebSocket,
    session_id: str,
    user_id: str = Depends(require_user_ws),
    db: AsyncSession = Depends(get_db),
):
    session_uuid = UUID(session_id)

    result = await db.execute(
        select(WatchSession).where(WatchSession.id == session_uuid)
    )
    session = result.scalar_one_or_none()

    logging.debug(f"{session=}")

    if not session or session.status != "active":
        await websocket.close(code=4004)
        return


    logging.debug(f"{user_id=}")

    result = await db.execute(
        select(WatchSessionParticipant).where(
            WatchSessionParticipant.session_id == session_uuid,
            WatchSessionParticipant.user_id == user_id,
        )
    )
    participant = result.scalar_one_or_none()

    logging.debug(f"{participant=}")

    if not participant:
        await websocket.close(code=4003)
        return

    await manager.connect(session_id, websocket)

    try:
        # Send authoritative state
        await websocket.send_json({
            "type": "sync",
            "position": session.current_position,
            "is_playing": session.is_playing,
            "server_time": time.time(),
        })

        while True:
            data = await websocket.receive_json()
            logging.debug(data)
            message_type = data.get("type")

            if message_type == "play":
                session.current_position = float(data["position"])
                session.is_playing = True
                await db.commit()

                await manager.broadcast(session_id, websocket, {
                    "type": "sync",
                    "position": session.current_position,
                    "is_playing": True,
                    "server_time": time.time(),
                })

            elif message_type == "pause":
                session.current_position = float(data["position"])
                session.is_playing = False
                await db.commit()

                await manager.broadcast(session_id,  websocket, {
                    "type": "sync",
                    "position": session.current_position,
                    "is_playing": False,
                    "server_time": time.time(),
                })

            elif message_type == "seek":
                session.current_position = float(data["position"])
                await db.commit()

                await manager.broadcast(session_id, websocket, {
                    "type": "sync",
                    "position": session.current_position,
                    "is_playing": session.is_playing,
                    "server_time": time.time(),
                })

            elif message_type == "chat":
                message = data.get("message", "")

                await manager.broadcast(session_id,  websocket, {
                    "type": "chat",
                    "user_id": user_id,
                    "message": message,
                    "timestamp": time.time(),
                })

    except WebSocketDisconnect as e:
        logging.error(e)
        manager.disconnect(session_id, websocket)


# -----------------------------------------------------------------------------
# Create Watch Session
# -----------------------------------------------------------------------------

@ws_router.post("/watch-session", response_model=None)
async def create_watch_session(
    payload: CreateWatchSessionRequest,
    user_id: str = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    logging.debug(f"{user_id=}")

    # Validate movie exists
    result = await db.execute(
        select(FilmWork).where(FilmWork.id == UUID(payload.movie_id))
    )
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Check if there is already an active session for this movie
    result = await db.execute(
        select(WatchSession).where(
            WatchSession.movie_id == movie.id,
            WatchSession.status == "active"
        )
    )
    session = result.scalar_one_or_none()

    # If session exists, ensure the user is a participant
    if session:
        result = await db.execute(
            select(WatchSessionParticipant).where(
                WatchSessionParticipant.session_id == session.id,
                WatchSessionParticipant.user_id == user_id,
            )
        )
        participant = result.scalar_one_or_none()

        if not participant:
            participant = WatchSessionParticipant(
                session_id=session.id,
                user_id=user_id,
                role="viewer",
            )
            db.add(participant)
            await db.commit()

        return {"session_id": str(session.id)}

    # Otherwise create a new session
    session = WatchSession(
        id=uuid4(),
        movie_id=movie.id,
        host_id=user_id,
        status="active",
        current_position=0.0,
        is_playing=False,
    )
    db.add(session)

    participant = WatchSessionParticipant(
        session_id=session.id,
        user_id=user_id,
        role="host",
    )
    db.add(participant)

    await db.commit()

    return {"session_id": str(session.id)}