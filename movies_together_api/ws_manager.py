from fastapi import WebSocket
from collections import defaultdict
from typing import Dict, Set


class SessionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = defaultdict(set)

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id].add(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket):
        self.active_connections[session_id].discard(websocket)
        if not self.active_connections[session_id]:
            del self.active_connections[session_id]

    async def broadcast(self, session_id: str, message: dict):
        for ws in list(self.active_connections.get(session_id, [])):
            await ws.send_json(message)