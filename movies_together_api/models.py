import uuid
from sqlalchemy import Column, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from db import Base


class WatchSession(Base):
    __tablename__ = "watch_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    movie_id = Column(UUID(as_uuid=True), nullable=False)
    host_id = Column(UUID(as_uuid=True), nullable=False)

    current_position = Column(Float, default=0)
    is_playing = Column(Boolean, default=False)

    status = Column(String, default="active")

    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())


class WatchSessionParticipant(Base):
    __tablename__ = "watch_session_participants"

    session_id = Column(UUID(as_uuid=True), ForeignKey("watch_sessions.id"))
    user_id = Column(UUID(as_uuid=True))