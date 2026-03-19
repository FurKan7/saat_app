-- Enable pgvector extension for vector similarity search
-- Note: This is already enabled in 001_initial_schema.sql, but kept here for safety
-- On Supabase, this is already available

CREATE EXTENSION IF NOT EXISTS vector;

-- Create HNSW index for fast approximate nearest neighbor search
-- Using cosine distance for similarity (1 - cosine_similarity)
-- Note: This will only work if watch_embeddings table exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'watch_embeddings') THEN
        CREATE INDEX IF NOT EXISTS idx_watch_embeddings_vector ON watch_embeddings 
        USING hnsw (embedding vector_cosine_ops);
    END IF;
END $$;

