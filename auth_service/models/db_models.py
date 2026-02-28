# SQLAlchemy ORM Models
# ---------------------------

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Enum as SAEnum,
    Integer,
    ForeignKey,
    Table,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base, relationship
import uuid
from datetime import datetime

from models.models import RoleType, SubscriptionStatus

Base = declarative_base()

# Association Table for User <-> Role
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("role_id", PGUUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    roles = relationship("Role", secondary=user_roles, back_populates="users")
    subscriptions = relationship("Subscription", back_populates="user")
    login_history = relationship("LoginHistory", back_populates="user")


class Role(Base):
    __tablename__ = "roles"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    permissions = Column(String)  # Comma-separated list of permissions
    type = Column(SAEnum(RoleType), default=RoleType.DEFAULT)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)

    users = relationship("User", secondary=user_roles, back_populates="roles")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    name = Column(String, nullable=False)
    description = Column(String)
    entitlements = Column(String)  # Comma-separated list
    status = Column(SAEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    price_cents = Column(Integer)
    duration_days = Column(Integer)
    started_at = Column(DateTime, default=datetime.utcnow)
    ends_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="subscriptions")


class LoginHistory(Base):
    __tablename__ = "login_history"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="login_history")
