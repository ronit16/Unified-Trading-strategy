CREATE TABLE IF NOT EXISTS live_strategies (
    strategy_id UUID PRIMARY KEY REFERENCES strategy_definitions(strategy_id),
    container_id VARCHAR(255) NOT NULL,
    deployed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
