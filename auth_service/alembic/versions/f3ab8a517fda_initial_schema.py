"""Initial schema with roles, users, subscriptions, user_roles, enum types"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql.base import UUID

# revision identifiers
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # -------------------------
    # EXTENSION
    # -------------------------
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # -------------------------
    # ENUMS
    # -------------------------
    roletype = postgresql.ENUM(
        "DEFAULT", "SYSTEM", "ADMIN", name="roletype", create_type=True
    )
    roletype.create(op.get_bind(), checkfirst=True)

    subscriptionstatus = postgresql.ENUM(
        "ACTIVE", "CANCELLED", "EXPIRED", name="subscriptionstatus", create_type=True
    )
    subscriptionstatus.create(op.get_bind(), checkfirst=True)

    # -------------------------
    # ROLES TABLE
    # -------------------------
    op.create_table(
        "roles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("name", sa.String(), unique=True, nullable=False),
        sa.Column("description", sa.String()),
        sa.Column("permissions", sa.String()),
        sa.Column(
            "type",
            sa.Enum("DEFAULT", "SYSTEM", "ADMIN", name="roletype"),
            server_default="DEFAULT",
        ),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True)),
    )

    # -------------------------
    # USERS TABLE
    # -------------------------
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("email", sa.String(), unique=True, nullable=False),
        sa.Column("full_name", sa.String()),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="TRUE"),
        sa.Column("is_superuser", sa.Boolean(), server_default="FALSE"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True)),
    )

    # -------------------------
    # USER-ROLES TABLE
    # -------------------------
    op.create_table(
        "user_roles",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # -------------------------
    # SUBSCRIPTIONS TABLE
    # -------------------------
    op.create_table(
        "subscriptions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String()),
        sa.Column("entitlements", sa.String()),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "CANCELLED", "EXPIRED", name="subscriptionstatus"),
            server_default="ACTIVE",
        ),
        sa.Column("price_cents", sa.Integer()),
        sa.Column("duration_days", sa.Integer()),
        sa.Column(
            "started_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column("ends_at", sa.TIMESTAMP(timezone=True)),
    )
    op.create_table(
        "login_history",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )


def downgrade():
    op.drop_table("subscriptions")
    op.drop_table("user_roles")
    op.drop_table("users")
    op.drop_table("roles")
    op.drop_table("login_history")
    op.execute("DROP TYPE IF EXISTS subscriptionstatus;")
    op.execute("DROP TYPE IF EXISTS roletype;")

    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp";')
