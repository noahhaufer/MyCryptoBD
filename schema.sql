-- Multi-user database schema for Telegram Contacts Tracker Mini App

-- Users table (Telegram users who use the app)
CREATE TABLE users (
    telegram_user_id BIGINT PRIMARY KEY,  -- Telegram user ID
    username TEXT,                         -- Telegram username
    first_name TEXT,
    last_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- User settings and credentials
CREATE TABLE user_settings (
    user_id BIGINT PRIMARY KEY REFERENCES users(telegram_user_id) ON DELETE CASCADE,

    -- Google Sheets settings
    google_sheet_name TEXT,
    google_refresh_token TEXT,          -- OAuth refresh token (encrypted)
    google_access_token TEXT,            -- OAuth access token (encrypted)
    google_token_expiry TIMESTAMP,

    -- Telegram session settings
    telegram_session_string TEXT,        -- Telethon session (encrypted)
    telegram_phone_number TEXT,          -- For reference only
    is_telegram_connected BOOLEAN DEFAULT FALSE,

    -- App settings
    auto_track_enabled BOOLEAN DEFAULT TRUE,
    initial_messages_count INTEGER DEFAULT 5,
    notification_enabled BOOLEAN DEFAULT TRUE,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tracked contacts (per user)
CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(telegram_user_id) ON DELETE CASCADE,
    contact_telegram_id BIGINT NOT NULL,  -- The contact's Telegram ID

    -- Contact information
    first_seen TIMESTAMP NOT NULL,
    name TEXT,
    username TEXT,
    company TEXT,
    role TEXT,
    bio TEXT,
    event_tag TEXT,
    last_contact TIMESTAMP,
    notes TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_to_sheets BOOLEAN DEFAULT FALSE,

    -- Ensure one contact per user (no duplicates)
    UNIQUE(user_id, contact_telegram_id)
);

-- Sync log (per user operations)
CREATE TABLE sync_log (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(telegram_user_id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL,
    details TEXT,
    status TEXT DEFAULT 'success'  -- success, failed, pending
);

-- API keys and credentials (for app-level services)
CREATE TABLE app_config (
    key TEXT PRIMARY KEY,
    value TEXT,
    encrypted BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_contacts_user_id ON contacts(user_id);
CREATE INDEX idx_contacts_first_seen ON contacts(first_seen);
CREATE INDEX idx_contacts_event_tag ON contacts(event_tag);
CREATE INDEX idx_contacts_synced ON contacts(synced_to_sheets);
CREATE INDEX idx_sync_log_user_id ON sync_log(user_id);
CREATE INDEX idx_sync_log_timestamp ON sync_log(timestamp);
CREATE INDEX idx_users_is_active ON users(is_active);

-- Comments for documentation
COMMENT ON TABLE users IS 'Telegram users who have started the bot and use the Mini App';
COMMENT ON TABLE user_settings IS 'Per-user settings including OAuth tokens and Telegram session';
COMMENT ON TABLE contacts IS 'Tracked contacts for each user (multi-tenant)';
COMMENT ON TABLE sync_log IS 'Audit log of sync operations per user';
COMMENT ON TABLE app_config IS 'Application-level configuration (OpenAI API key, etc.)';
