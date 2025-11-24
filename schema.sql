-- Simple Neon PostgreSQL Schema for YouTube Sentiment Analyzer
-- Synchronous, minimal design for capstone demo

-- Users table: stores Google OAuth users
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_email ON users(email);

-- Videos table: stores YouTube video metadata
CREATE TABLE IF NOT EXISTS videos (
    video_id SERIAL PRIMARY KEY,
    youtube_video_id VARCHAR(100) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    title TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_videos_youtube_id ON videos(youtube_video_id);
CREATE INDEX idx_videos_user_id ON videos(user_id);

-- Analyses table: stores sentiment analysis results
CREATE TABLE IF NOT EXISTS analyses (
    analysis_id SERIAL PRIMARY KEY,
    video_id INTEGER REFERENCES videos(video_id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    total_comments INTEGER DEFAULT 0,
    positive_count INTEGER DEFAULT 0,
    negative_count INTEGER DEFAULT 0,
    neutral_count INTEGER DEFAULT 0,
    positive_percentage NUMERIC(5,2),
    negative_percentage NUMERIC(5,2),
    neutral_percentage NUMERIC(5,2),
    top_negative_comments TEXT,  -- JSON string of top 5 negative comments
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_analyses_video_id ON analyses(video_id);
CREATE INDEX idx_analyses_user_id ON analyses(user_id);

-- Comments table: stores raw YouTube comments
CREATE TABLE IF NOT EXISTS comments (
    comment_id SERIAL PRIMARY KEY,
    video_id INTEGER REFERENCES videos(video_id) ON DELETE CASCADE,
    author VARCHAR(255) NOT NULL,
    text TEXT NOT NULL,
    sentiment VARCHAR(20),  -- POSITIVE, NEGATIVE, NEUTRAL
    confidence NUMERIC(5,4),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_comments_video_id ON comments(video_id);
CREATE INDEX idx_comments_sentiment ON comments(sentiment);