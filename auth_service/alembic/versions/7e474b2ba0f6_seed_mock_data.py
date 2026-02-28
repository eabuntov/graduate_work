"""Seed mock roles, users, assignments, subscriptions"""

from alembic import op
from sqlalchemy.sql import text

# revision identifiers
revision = "0002_mock_data"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # ROLES
    conn.execute(
        text("""
        INSERT INTO roles (id, name, description, permissions, type) VALUES
            ('00000000-0000-0000-0000-000000000001', 'user', 'Basic user role', 'read:public_content,watch:movies', 'DEFAULT'),
            ('00000000-0000-0000-0000-000000000002', 'premium', 'Premium subscription role', 'read:public_content,watch:movies', 'DEFAULT'),
            ('00000000-0000-0000-0000-000000000003', 'admin', 'Administrator role', 'manage:users,manage:roles,manage:subscriptions,view:admin_panel', 'ADMIN'),
            ('00000000-0000-0000-0000-000000000004', 'system', 'System-level operations', 'manage:subscriptions', 'SYSTEM');
    """)
    )

    # USERS
    conn.execute(
        text("""
        INSERT INTO users (id, email, full_name, password_hash, is_superuser) VALUES
            ('10000000-0000-0000-0000-000000000001', 'alice@example.com', 'Alice Johnson', 'hash1', FALSE),
            ('10000000-0000-0000-0000-000000000002', 'bob@example.com', 'Bob Smith', 'hash2', FALSE),
            ('10000000-0000-0000-0000-000000000003', 'carol@example.com', 'Carol White', 'hash3', FALSE),
            ('10000000-0000-0000-0000-000000000004', 'admin@example.com', 'Admin Guy', 'hash_admin', TRUE),
            ('10000000-0000-0000-0000-000000000005', 'system@example.com', 'System Account', 'hash_sys', TRUE);
    """)
    )

    # USER ROLES
    conn.execute(
        text("""
        INSERT INTO user_roles (user_id, role_id) VALUES
            ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001'),
            ('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001'),
            ('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000002'),
            ('10000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001'),
            ('10000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000003'),
            ('10000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000004');
    """)
    )

    # SUBSCRIPTIONS
    conn.execute(
        text("""
        INSERT INTO subscriptions (id, user_id, name, description, entitlements, status, price_cents, duration_days, ends_at)
        VALUES
            (uuid_generate_v4(),'10000000-0000-0000-0000-000000000001','Basic Plan','Access to SD streaming','sd_streaming','ACTIVE',999,30,NOW() + INTERVAL '30 days'),
            (uuid_generate_v4(),'10000000-0000-0000-0000-000000000002','Premium Plan','Full access including HD','sd_streaming,hd_streaming,4k_streaming','ACTIVE',1999,30,NOW() + INTERVAL '30 days'),
            (uuid_generate_v4(),'10000000-0000-0000-0000-000000000002','Sports Add-on','Access to live sports','sports','ACTIVE',499,30,NOW() + INTERVAL '30 days'),
            (uuid_generate_v4(),'10000000-0000-0000-0000-000000000003','Basic Plan','Access to SD streaming','sd_streaming','CANCELLED',999,30,NOW() - INTERVAL '5 days'),
            (uuid_generate_v4(),'10000000-0000-0000-0000-000000000003','Kids Pack','Kids-only safe content','kids','ACTIVE',299,30,NOW() + INTERVAL '30 days'),
            (uuid_generate_v4(),'10000000-0000-0000-0000-000000000004','Admin Premium','Admin full entitlement','admin_tools,hd_streaming,4k_streaming','ACTIVE',0,365,NOW() + INTERVAL '365 days'),
            (uuid_generate_v4(),'10000000-0000-0000-0000-000000000005','System Subscription','Internal system processes','system_access','ACTIVE',0,365,NOW() + INTERVAL '365 days');
    """)
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(text("DELETE FROM subscriptions;"))
    conn.execute(text("DELETE FROM user_roles;"))
    conn.execute(text("DELETE FROM users;"))
    conn.execute(text("DELETE FROM roles;"))
