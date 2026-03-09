import uuid

from sqlalchemy import String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy import (
    Column,
    Text,
    CheckConstraint,
    ForeignKey,
    DateTime,
    Date,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from pydantic import BaseModel

from db import Base

class FilmWork(Base):
    __tablename__ = "film_works"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    title = Column(
        Text,
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    creation_date = Column(
        Date,
        nullable=True,
    )

    rating = Column(
        Float,
        nullable=True,
    )

    type = Column(
        Text,
        nullable=False,
    )

    created = Column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
    )

    modified = Column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint("length(title) > 0", name="ck_filmwork_title_not_empty"),
        CheckConstraint("length(type) > 0", name="ck_filmwork_type_not_empty"),
    )

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

    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("watch_sessions.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    role = Column(
        Text,
        nullable=False,
        server_default=text("'member'"),
    )

    joined_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('host', 'member')",
            name="ck_wsp_role",
        ),
    )

    # Optional relationships
    session = relationship(
        "WatchSession",
        back_populates="participants",
        passive_deletes=True,
    )

    user = relationship(
        "User",
        back_populates="watch_sessions",
        passive_deletes=True,
    )

class CreateWatchSessionRequest(BaseModel):
    movie_id: str