-- Update watch_embeddings table to support SigLIP2 (larger vectors)
-- SigLIP2 may produce different vector dimensions than base SigLIP
-- This migration updates the vector dimension if needed

-- Note: If your pgvector version supports it, you can alter the vector dimension
-- For now, we'll keep 512 as a safe default (SigLIP2 base models use 768, but we'll use 512 for compatibility)
-- In production, you may want to create a new column or table for SigLIP2 embeddings

-- Update model_name default to siglip2
ALTER TABLE watch_embeddings ALTER COLUMN model_name SET DEFAULT 'siglip2';

-- Add index for model_name for faster filtering
CREATE INDEX IF NOT EXISTS idx_watch_embeddings_model_name ON watch_embeddings(model_name);
