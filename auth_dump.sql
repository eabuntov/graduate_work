-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

------------------------------------------------------------
-- ENUM TYPES
------------------------------------------------------------

-- Role type enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'roletype') THEN
        CREATE TYPE RoleType AS ENUM ('DEFAULT', 'SYSTEM', 'ADMIN');
    END IF;
END$$;

-- Subscription status enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subscriptionstatus') THEN
        CREATE TYPE SubscriptionStatus AS ENUM ('ACTIVE', 'CANCELLED', 'EXPIRED');
    END IF;
END$$;

------------------------------------------------------------
-- TABLES
------------------------------------------------------------

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR UNIQUE NOT NULL,
    description VARCHAR,
    permissions VARCHAR,
    type RoleType DEFAULT 'DEFAULT',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR UNIQUE NOT NULL,
    full_name VARCHAR,
    password_hash VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    description VARCHAR,
    entitlements VARCHAR,
    status SubscriptionStatus DEFAULT 'ACTIVE',
    price_cents INTEGER,
    duration_days INTEGER,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ends_at TIMESTAMPTZ
);

CREATE TABLE login_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    ip_address VARCHAR,
    user_agent VARCHAR,

    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

------------------------------------------------------------
-- MOCK DATA
------------------------------------------------------------

------------------------------------------------------------
-- ROLES
------------------------------------------------------------
INSERT INTO roles (id, name, description, permissions, type)
VALUES
    (
        '00000000-0000-0000-0000-000000000001',
         'user', 'Basic user role',
         'read:public_content,watch:movies',
         'DEFAULT'
    ),
    (
        '00000000-0000-0000-0000-000000000002',
        'premium',
        'Premium subscription role',
        'read:public_content,watch:movies',
        'DEFAULT'
    ),
    (
        '00000000-0000-0000-0000-000000000003',
        'admin',
        'Administrator role',
        'manage:users,manage:roles,manage:subscriptions,view:admin_panel',
        'ADMIN'
    ),
    (
        '00000000-0000-0000-0000-000000000004',
        'system',
        'System-level operations',
        'manage:subscriptions',
        'SYSTEM'
    );

------------------------------------------------------------
-- USERS
------------------------------------------------------------
INSERT INTO users (id, email, full_name, password_hash, is_superuser)
VALUES
    ('10000000-0000-0000-0000-000000000001', 'alice@example.com', 'Alice Johnson', 'hash1', FALSE),
    ('10000000-0000-0000-0000-000000000002', 'bob@example.com', 'Bob Smith', 'hash2', FALSE),
    ('10000000-0000-0000-0000-000000000003', 'carol@example.com', 'Carol White', 'hash3', FALSE),
    ('10000000-0000-0000-0000-000000000004', 'admin@example.com', 'Admin Guy', 'hash_admin', TRUE),
    ('10000000-0000-0000-0000-000000000005', 'system@example.com', 'System Account', 'hash_sys', TRUE);

------------------------------------------------------------
-- USER → ROLE ASSIGNMENTS
------------------------------------------------------------
INSERT INTO user_roles (user_id, role_id)
VALUES
    ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001'), -- Alice: user
    ('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001'), -- Bob: user
    ('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000002'), -- Bob: premium
    ('10000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001'), -- Carol: user
    ('10000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000003'), -- Admin
    ('10000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000004'); -- System

------------------------------------------------------------
-- SUBSCRIPTIONS
------------------------------------------------------------

INSERT INTO subscriptions (id, user_id, name, description, entitlements, status, price_cents, duration_days, ends_at)
VALUES
    (uuid_generate_v4(), '10000000-0000-0000-0000-000000000001', 'Basic Plan', 'Access to SD streaming', 'sd_streaming', 'ACTIVE', 999, 30, NOW() + INTERVAL '30 days'),

    (uuid_generate_v4(), '10000000-0000-0000-0000-000000000002', 'Premium Plan', 'Full access including HD', 'sd_streaming,hd_streaming,4k_streaming', 'ACTIVE', 1999, 30, NOW() + INTERVAL '30 days'),

    (uuid_generate_v4(), '10000000-0000-0000-0000-000000000002', 'Sports Add-on', 'Access to live sports', 'sports', 'ACTIVE', 499, 30, NOW() + INTERVAL '30 days'),

    (uuid_generate_v4(), '10000000-0000-0000-0000-000000000003', 'Basic Plan', 'Access to SD streaming', 'sd_streaming', 'CANCELLED', 999, 30, NOW() - INTERVAL '5 days'),

    (uuid_generate_v4(), '10000000-0000-0000-0000-000000000003', 'Kids Pack', 'Kids-only safe content', 'kids', 'ACTIVE', 299, 30, NOW() + INTERVAL '30 days'),

    (uuid_generate_v4(), '10000000-0000-0000-0000-000000000004', 'Admin Premium', 'Admin full entitlement', 'admin_tools,hd_streaming,4k_streaming', 'ACTIVE', 0, 365, NOW() + INTERVAL '365 days'),

    (uuid_generate_v4(), '10000000-0000-0000-0000-000000000005', 'System Subscription', 'Internal system processes', 'system_access', 'ACTIVE', 0, 365, NOW() + INTERVAL '365 days');
