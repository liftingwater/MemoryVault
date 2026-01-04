-- MemoryVault Database Schema
-- PostgreSQL / SQLite compatible

-- Enable UUID extension (PostgreSQL only)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    storage_used_bytes BIGINT DEFAULT 0,
    storage_quota_bytes BIGINT DEFAULT 1073741824,  -- 1GB default
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Decks table
CREATE TABLE decks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_deck_name_per_user UNIQUE(user_id, name)
);

-- Media files table
CREATE TABLE media_files (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_type VARCHAR(20) NOT NULL CHECK (file_type IN ('image', 'audio')),
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) UNIQUE NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    alt_text TEXT,
    duration_seconds FLOAT,
    thumbnail_path VARCHAR(500),
    storage_provider VARCHAR(50) DEFAULT 'local',
    storage_url TEXT,
    checksum VARCHAR(64) NOT NULL,
    reference_count INTEGER DEFAULT 0,  -- Track how many cards use this file
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cards table
CREATE TABLE cards (
    id SERIAL PRIMARY KEY,
    deck_id INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    box_number INTEGER DEFAULT 1 CHECK (box_number BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_reviewed TIMESTAMP,
    review_count INTEGER DEFAULT 0,
    next_review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ease_factor FLOAT DEFAULT 2.5,
    interval_days INTEGER DEFAULT 1,
    is_suspended BOOLEAN DEFAULT FALSE
);

-- Card content table (supports multiple content items per side)
CREATE TABLE card_content (
    id SERIAL PRIMARY KEY,
    card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    side VARCHAR(10) NOT NULL CHECK (side IN ('front', 'back')),
    content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('text', 'image', 'audio')),
    text_content TEXT,
    media_file_id INTEGER REFERENCES media_files(id) ON DELETE SET NULL,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT content_has_value CHECK (
        (content_type = 'text' AND text_content IS NOT NULL) OR
        (content_type IN ('image', 'audio') AND media_file_id IS NOT NULL)
    )
);

-- Review history table
CREATE TABLE review_history (
    id SERIAL PRIMARY KEY,
    card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    was_correct BOOLEAN NOT NULL,
    previous_box INTEGER NOT NULL,
    new_box INTEGER NOT NULL,
    response_time_ms INTEGER,
    difficulty_rating INTEGER CHECK (difficulty_rating BETWEEN 1 AND 5),
    ease_factor FLOAT,
    interval_days INTEGER
);

-- Tags table
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7) DEFAULT '#6366f1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_tag_per_user UNIQUE(user_id, name)
);

-- Card tags junction table
CREATE TABLE card_tags (
    card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (card_id, tag_id)
);

-- Indexes for performance
CREATE INDEX idx_decks_user_id ON decks(user_id);
CREATE INDEX idx_cards_deck_id ON cards(deck_id);
CREATE INDEX idx_cards_box_number ON cards(box_number);
CREATE INDEX idx_cards_next_review ON cards(next_review_date) WHERE is_suspended = FALSE;
CREATE INDEX idx_card_content_card_id ON card_content(card_id);
CREATE INDEX idx_card_content_media_file ON card_content(media_file_id);
CREATE INDEX idx_media_files_user_id ON media_files(user_id);
CREATE INDEX idx_media_files_checksum ON media_files(checksum);
CREATE INDEX idx_review_history_card_id ON review_history(card_id);
CREATE INDEX idx_review_history_date ON review_history(reviewed_at);
CREATE INDEX idx_tags_user_id ON tags(user_id);

-- Triggers for updated_at (PostgreSQL)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_decks_updated_at BEFORE UPDATE ON decks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update storage usage when files are added/removed
CREATE OR REPLACE FUNCTION update_user_storage()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE users SET storage_used_bytes = storage_used_bytes + NEW.file_size
        WHERE id = NEW.user_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE users SET storage_used_bytes = storage_used_bytes - OLD.file_size
        WHERE id = OLD.user_id;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_storage_on_insert AFTER INSERT ON media_files
    FOR EACH ROW EXECUTE FUNCTION update_user_storage();

CREATE TRIGGER update_storage_on_delete AFTER DELETE ON media_files
    FOR EACH ROW EXECUTE FUNCTION update_user_storage();

