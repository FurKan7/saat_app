-- Watch Community Platform - Social Step 1 (v1)
-- User profiles: collections + items + AI/admin watch suggestions

-- User collections: users can group watches they love
CREATE TABLE IF NOT EXISTS user_collections (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_collections_user_id ON user_collections(user_id);

-- Watch suggestions: pending AI output + admin approval for watch_core creation
CREATE TABLE IF NOT EXISTS watch_suggestions (
    id SERIAL PRIMARY KEY,
    submitted_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('pending_admin', 'approved', 'rejected')),

    -- Strong identifiers (used to check if watch already exists)
    sku TEXT,
    source TEXT,
    product_url TEXT,
    product_name TEXT,
    brand TEXT,
    image_url TEXT,

    -- AI output stored as JSON
    ai_output_json JSONB,

    admin_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_watch_suggestions_status ON watch_suggestions(status);
CREATE INDEX IF NOT EXISTS idx_watch_suggestions_submitted_by ON watch_suggestions(submitted_by);

-- Items inside a user's collection (can be linked to an existing watch_core or pending a suggestion)
CREATE TABLE IF NOT EXISTS user_collection_items (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER NOT NULL REFERENCES user_collections(id) ON DELETE CASCADE,

    status TEXT NOT NULL CHECK (
        status IN (
            'processing_ai',
            'matched_existing',
            'pending_admin',
            'approved_linked',
            'rejected'
        )
    ),

    -- identifiers provided by user (also used by background existence check)
    sku TEXT,
    source TEXT,
    product_url TEXT,
    product_name TEXT,
    brand TEXT,
    image_url TEXT,

    -- links after background/admin approval
    watch_id INTEGER REFERENCES watch_core(watch_id) ON DELETE SET NULL,
    suggestion_id INTEGER REFERENCES watch_suggestions(id) ON DELETE SET NULL,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_collection_items_collection_id ON user_collection_items(collection_id);
CREATE INDEX IF NOT EXISTS idx_user_collection_items_status ON user_collection_items(status);

-- updated_at trigger helper (if it exists from earlier migrations)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.triggers
        WHERE event_object_table IN ('user_collections','watch_suggestions','user_collection_items')
    ) THEN
        -- ignore (already has triggers)
        NULL;
    ELSE
        IF EXISTS (
            SELECT 1 FROM pg_proc WHERE proname = 'update_updated_at_column'
        ) THEN
            CREATE TRIGGER update_user_collections_updated_at
            BEFORE UPDATE ON user_collections
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

            CREATE TRIGGER update_watch_suggestions_updated_at
            BEFORE UPDATE ON watch_suggestions
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

            CREATE TRIGGER update_user_collection_items_updated_at
            BEFORE UPDATE ON user_collection_items
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        END IF;
    END IF;
END $$;

