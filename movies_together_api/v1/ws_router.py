import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from db import get_db
from models import WatchSession, WatchSessionParticipant
from ws_manager import SessionManager

router = APIRouter()
manager = SessionManager()


# Replace with your actual auth mechanism
async def get_current_user_id(websocket: WebSocket) -> str:
    token = websocket.headers.get("authorization")
    if not token:
        raise HTTPException(status_code=401)
    # validate token...
    return "mock-user-id"


@router.websocket("/ws/watch/{session_id}")
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