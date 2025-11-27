CREATE TABLE IF NOT EXISTS backtest_runs (
    run_id UUID PRIMARY KEY,
    strategy_id UUID REFERENCES strategy_definitions(strategy_id),
    iteration_number INTEGER,
    parameters_used JSONB,
    sharpe_ratio DECIMAL,
    max_drawdown DECIMAL,
    final_equity DECIMAL,
    passed_criteria BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
