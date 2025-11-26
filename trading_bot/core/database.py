import asyncpg
import logging

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
        query = """
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
        async with self.pool.acquire() as conn:
            await conn.execute(query)

    async def save_trade(self, symbol, side, price, amount, mode, strategy):
        query = """
        INSERT INTO trades (symbol, side, price, amount, mode, strategy)
        VALUES ($1, $2, $3, $4, $5, $6)
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, symbol, side, price, amount, mode, strategy)
            logger.info(f"Trade saved to DB: {side} {symbol}")

    async def close(self):
        if self.pool:
            await self.pool.close()