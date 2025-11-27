import asyncpg
import logging
import uuid
import json

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_url):
        self.db_url = db_url
        self.pool = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(self.db_url)
            await self._init_tables()
            logger.info("Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    async def _init_tables(self):
        async with self.pool.acquire() as conn:
            # Initialize trades table (existing)
            trades_query = """
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                symbol VARCHAR(20),
                side VARCHAR(20),
                price DECIMAL,
                amount DECIMAL,
                mode VARCHAR(10),
                strategy VARCHAR(20)
            );
            """
            await conn.execute(trades_query)

            # Initialize strategy_definitions table
            with open('trading_bot/core/sql/schema.sql', 'r') as f:
                schema_query = f.read()
            await conn.execute(schema_query)

            # Initialize backtest_runs table
            with open('trading_bot/core/sql/backtest_runs.sql', 'r') as f:
                backtest_schema_query = f.read()
            await conn.execute(backtest_schema_query)

            # Initialize live_strategies table
            with open('trading_bot/core/sql/live_strategies.sql', 'r') as f:
                live_schema_query = f.read()
            await conn.execute(live_schema_query)

    async def save_trade(self, symbol, side, price, amount, mode, strategy):
        query = """
        INSERT INTO trades (symbol, side, price, amount, mode, strategy)
        VALUES ($1, $2, $3, $4, $5, $6)
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, symbol, side, price, amount, mode, strategy)
            logger.info(f"Trade saved to DB: {side} {symbol}")

    async def save_strategy(self, source_url: str, raw_text: str, structured_json: dict) -> str:
        """Saves a new strategy definition to the database and returns its ID."""
        strategy_id = uuid.uuid4()
        json_str = json.dumps(structured_json) # Convert dict to JSON string for DB
        query = """
        INSERT INTO strategy_definitions (strategy_id, source_url, raw_text, structured_json)
        VALUES ($1, $2, $3, $4)
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, strategy_id, source_url, raw_text, json_str)
            logger.info(f"Strategy saved to DB with ID: {strategy_id}")
        return str(strategy_id)

    async def save_backtest_run(self, strategy_id: str, iteration: int, params: dict, results: dict) -> str:
        """Saves the results of a backtest run to the database."""
        run_id = uuid.uuid4()
        params_json = json.dumps(params)
        query = """
        INSERT INTO backtest_runs (run_id, strategy_id, iteration_number, parameters_used,
                                   sharpe_ratio, max_drawdown, final_equity, passed_criteria)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, run_id, uuid.UUID(strategy_id), iteration, params_json,
                               results.get('sharpe_ratio'), results.get('max_drawdown'),
                               results.get('final_equity'), results.get('passed_criteria'))
            logger.info(f"Backtest run saved to DB with ID: {run_id}")
        return str(run_id)

    async def add_live_strategy(self, strategy_id: str, container_id: str):
        """Adds a new live strategy to the database."""
        query = """
        INSERT INTO live_strategies (strategy_id, container_id)
        VALUES ($1, $2)
        ON CONFLICT (strategy_id) DO UPDATE SET container_id = $2;
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, uuid.UUID(strategy_id), container_id)
            logger.info(f"Live strategy {strategy_id} with container {container_id} saved to DB.")

    async def get_live_strategies(self) -> dict:
        """Retrieves a mapping of all live strategies and their container IDs."""
        query = "SELECT strategy_id, container_id FROM live_strategies;"
        async with self.pool.acquire() as conn:
            records = await conn.fetch(query)
        return {str(record['strategy_id']): record['container_id'] for record in records}

    async def close(self):
        if self.pool:
            await self.pool.close()