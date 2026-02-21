-- ============================================================
-- Enable UUID generation (if not already enabled)
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ============================================================
-- USERS
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- FRIENDSHIPS
-- Symmetric friendship represented as directed rows
-- ============================================================

CREATE TABLE IF NOT EXISTS friendships (
    user_id UUID NOT NULL,
    friend_id UUID NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'accepted', 'blocked')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (user_id, friend_id),

    CONSTRAINT fk_friendships_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_friendships_friend
        FOREIGN KEY (friend_id) REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_not_self_friend
        CHECK (user_id <> friend_id)
);

CREATE INDEX IF NOT EXISTS idx_friendships_status
    ON friendships (user_id, status);


-- ============================================================
-- MOVIES
-- ============================================================

CREATE TABLE IF NOT EXISTS movies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    video_url TEXT NOT NULL,
    poster_url TEXT,
    duration_seconds INTEGER NOT NULL CHECK (duration_seconds > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_movies_title
    ON movies (title);


-- ============================================================
-- WANT TO WATCH LIST
-- ============================================================

CREATE TABLE IF NOT EXISTS want_to_watch (
    user_id UUID NOT NULL,
    movie_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (user_id, movie_id),

    CONSTRAINT fk_wtw_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_wtw_movie
        FOREIGN KEY (movie_id) REFERENCES movies(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_wtw_movie
    ON want_to_watch (movie_id);


-- ============================================================
-- WATCH SESSIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS watch_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    movie_id UUID NOT NULL,
    host_id UUID NOT NULL,

    current_position DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (current_position >= 0),
    is_playing BOOLEAN NOT NULL DEFAULT FALSE,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'ended')),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_session_movie
        FOREIGN KEY (movie_id) REFERENCES movies(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_session_host
        FOREIGN KEY (host_id) REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_watch_sessions_status
    ON watch_sessions (status);

CREATE INDEX IF NOT EXISTS idx_watch_sessions_movie
    ON watch_sessions (movie_id);


-- ============================================================
-- WATCH SESSION PARTICIPANTS
-- ============================================================

CREATE TABLE IF NOT EXISTS watch_session_participants (
    session_id UUID NOT NULL,
    user_id UUID NOT NULL,
    role TEXT NOT NULL DEFAULT 'member'
        CHECK (role IN ('host', 'member')),
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (session_id, user_id),

    CONSTRAINT fk_wsp_session
        FOREIGN KEY (session_id) REFERENCES watch_sessions(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_wsp_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_wsp_user
    ON watch_session_participants (user_id);


-- ============================================================
-- CHAT MESSAGES
-- ============================================================

CREATE TABLE IF NOT EXISTS watch_session_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL,
    user_id UUID NOT NULL,
    message TEXT NOT NULL CHECK (length(message) <= 2000),
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_msg_session
        FOREIGN KEY (session_id) REFERENCES watch_sessions(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_msg_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_session_time
    ON watch_session_messages (session_id, sent_at);