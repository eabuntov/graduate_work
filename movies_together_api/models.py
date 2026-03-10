import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Boolean,
    Float,
    DateTime,
    Date,
    Text,
    CheckConstraint,
    ForeignKey,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from pydantic import BaseModel

from db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # sessions this user participates in
    watch_sessions = relationship(
        "WatchSessionParticipant",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class FilmWork(Base):
    __tablename__ = "film_work"
    __table_args__ = (
        CheckConstraint("length(title) > 0", name="ck_filmwork_title_not_empty"),
        CheckConstraint("length(type) > 0", name="ck_filmwork_type_not_empty"),
        {"schema": "content"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    title = Column(Text, nullable=False)
    description = Column(Text)
    creation_date = Column(Date)
    rating = Column(Float)
    type = Column(Text, nullable=False)

    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FilmWorkStorage(Base):
    __tablename__ = "film_work_storage"
    __table_args__ = {"schema": "content"}

    film_work_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.film_work.id"),
        primary_key=True,
        nullable=False
    )

    video_url: Mapped[str] = mapped_column(
        String,
        nullable=False
    )


class WatchSession(Base):
    __tablename__ = "watch_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    movie_id = Column(
        UUID(as_uuid=True),
        ForeignKey("content.film_work.id"),
        nullable=False,
    )

    host_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    current_position = Column(Float, default=0)
    is_playing = Column(Boolean, default=False)

    status = Column(String, default="active")

    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())

    # participants in the session
    participants = relationship(
        "WatchSessionParticipant",
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # optional: easy access to movie
    movie = relationship("FilmWork")

    # optional: host user
    host = relationship("User")


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

    # relationships
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