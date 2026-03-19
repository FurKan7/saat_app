-- Watch Community Platform - Initial Schema
-- Supports community contributions, voting, AI estimations, and vector search

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgvector extension (MUST be enabled before creating tables with vector columns)
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table (minimal profile, Supabase Auth handles authentication)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supabase_user_id UUID UNIQUE NOT NULL, -- Links to Supabase Auth
    username VARCHAR(100),
    display_name VARCHAR(200),
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Watch core table (immutable seed data)
CREATE TABLE IF NOT EXISTS watch_core (
    watch_id SERIAL PRIMARY KEY,
    source VARCHAR(255) NOT NULL,
    product_url TEXT NOT NULL,
    image_url TEXT, -- Can contain multiple URLs separated by spaces
    brand VARCHAR(255),
    product_name VARCHAR(500) NOT NULL,
    sku VARCHAR(255),
    price_raw VARCHAR(100),
    price_value DECIMAL(12, 2),
    currency VARCHAR(3) DEFAULT 'TRY' CHECK (currency IN ('TRY', 'USD', 'EUR', 'GBP')),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Watch spec state (current "best known" resolved value per spec)
CREATE TABLE IF NOT EXISTS watch_spec_state (
    id SERIAL PRIMARY KEY,
    watch_id INTEGER NOT NULL REFERENCES watch_core(watch_id) ON DELETE CASCADE,
    spec_key VARCHAR(100) NOT NULL, -- e.g., 'case_diameter_mm', 'weight_g', 'gender'
    spec_value TEXT, -- Stored as text, can be numeric or categorical
    unit VARCHAR(50), -- e.g., 'mm', 'g', 'atm'
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('official', 'community_verified', 'ai_estimated', 'disputed', 'unknown')),
    confidence DECIMAL(3, 2), -- 0.00 to 1.00, for AI estimations
    resolved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(watch_id, spec_key)
);

-- Watch spec sources (traceability: which source provided which value)
CREATE TABLE IF NOT EXISTS watch_spec_sources (
    id SERIAL PRIMARY KEY,
    watch_id INTEGER NOT NULL REFERENCES watch_core(watch_id) ON DELETE CASCADE,
    spec_key VARCHAR(100) NOT NULL,
    spec_value TEXT NOT NULL,
    unit VARCHAR(50),
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('official', 'scraper', 'community', 'ai')),
    source_name VARCHAR(255) NOT NULL, -- e.g., 'abtsaat.com', 'user_123', 'openai_clip'
    source_url TEXT, -- URL to evidence
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(watch_id, spec_key, source_type, source_name, spec_value)
);

-- Watch comments/reviews
CREATE TABLE IF NOT EXISTS watch_comments (
    id SERIAL PRIMARY KEY,
    watch_id INTEGER NOT NULL REFERENCES watch_core(watch_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5), -- Optional 1-5 star rating
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Watch user contributions (user-proposed spec values)
CREATE TABLE IF NOT EXISTS watch_user_contributions (
    id SERIAL PRIMARY KEY,
    watch_id INTEGER NOT NULL REFERENCES watch_core(watch_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    spec_key VARCHAR(100) NOT NULL,
    proposed_value TEXT NOT NULL,
    unit VARCHAR(50),
    note TEXT, -- User's explanation
    evidence_url TEXT, -- URL to evidence (image, link, etc.)
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Watch contribution votes (confirm/reject votes)
CREATE TABLE IF NOT EXISTS watch_contribution_votes (
    id SERIAL PRIMARY KEY,
    contribution_id INTEGER NOT NULL REFERENCES watch_user_contributions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    vote_type VARCHAR(20) NOT NULL CHECK (vote_type IN ('confirm', 'reject')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(contribution_id, user_id) -- One vote per user per contribution
);

-- Watch AI estimations (AI-estimated values, never overwrites official)
CREATE TABLE IF NOT EXISTS watch_ai_estimations (
    id SERIAL PRIMARY KEY,
    watch_id INTEGER NOT NULL REFERENCES watch_core(watch_id) ON DELETE CASCADE,
    spec_key VARCHAR(100) NOT NULL,
    estimated_value TEXT NOT NULL,
    unit VARCHAR(50),
    confidence DECIMAL(3, 2) NOT NULL CHECK (confidence >= 0.00 AND confidence <= 1.00),
    model_name VARCHAR(255) NOT NULL, -- e.g., 'siglip', 'clip', 'gpt4v'
    model_version VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(watch_id, spec_key, model_name)
);

-- Watch embeddings (vector embeddings for similarity search)
CREATE TABLE IF NOT EXISTS watch_embeddings (
    id SERIAL PRIMARY KEY,
    watch_id INTEGER NOT NULL REFERENCES watch_core(watch_id) ON DELETE CASCADE,
    embedding vector(512), -- SigLIP produces 512-dim vectors
    text_payload TEXT, -- The text that was embedded (brand + product_name + key specs)
    model_name VARCHAR(255) NOT NULL DEFAULT 'siglip',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(watch_id, model_name)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_watch_core_brand ON watch_core(brand);
CREATE INDEX IF NOT EXISTS idx_watch_core_source ON watch_core(source);
CREATE INDEX IF NOT EXISTS idx_watch_spec_state_watch_id ON watch_spec_state(watch_id);
CREATE INDEX IF NOT EXISTS idx_watch_spec_state_spec_key ON watch_spec_state(spec_key);
CREATE INDEX IF NOT EXISTS idx_watch_spec_state_source_type ON watch_spec_state(source_type);
CREATE INDEX IF NOT EXISTS idx_watch_spec_sources_watch_id ON watch_spec_sources(watch_id);
CREATE INDEX IF NOT EXISTS idx_watch_spec_sources_spec_key ON watch_spec_sources(spec_key);
CREATE INDEX IF NOT EXISTS idx_watch_comments_watch_id ON watch_comments(watch_id);
CREATE INDEX IF NOT EXISTS idx_watch_comments_user_id ON watch_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_watch_user_contributions_watch_id ON watch_user_contributions(watch_id);
CREATE INDEX IF NOT EXISTS idx_watch_user_contributions_user_id ON watch_user_contributions(user_id);
CREATE INDEX IF NOT EXISTS idx_watch_user_contributions_status ON watch_user_contributions(status);
CREATE INDEX IF NOT EXISTS idx_watch_contribution_votes_contribution_id ON watch_contribution_votes(contribution_id);
CREATE INDEX IF NOT EXISTS idx_watch_contribution_votes_user_id ON watch_contribution_votes(user_id);
CREATE INDEX IF NOT EXISTS idx_watch_ai_estimations_watch_id ON watch_ai_estimations(watch_id);
CREATE INDEX IF NOT EXISTS idx_watch_ai_estimations_spec_key ON watch_ai_estimations(spec_key);
CREATE INDEX IF NOT EXISTS idx_watch_embeddings_watch_id ON watch_embeddings(watch_id);

-- Vector similarity index (HNSW for fast approximate nearest neighbor search)
-- This will be created after pgvector extension is enabled
-- CREATE INDEX IF NOT EXISTS idx_watch_embeddings_vector ON watch_embeddings 
-- USING hnsw (embedding vector_cosine_ops);

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_watch_core_updated_at BEFORE UPDATE ON watch_core
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_watch_spec_state_updated_at BEFORE UPDATE ON watch_spec_state
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_watch_comments_updated_at BEFORE UPDATE ON watch_comments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_watch_user_contributions_updated_at BEFORE UPDATE ON watch_user_contributions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_watch_embeddings_updated_at BEFORE UPDATE ON watch_embeddings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

