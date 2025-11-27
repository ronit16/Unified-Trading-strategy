CREATE TABLE IF NOT EXISTS strategy_definitions (
    strategy_id UUID PRIMARY KEY,
    source_url TEXT,
    raw_text TEXT,
    structured_json JSONB,
    status VARCHAR(20) DEFAULT 'DRAFT',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
