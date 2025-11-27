import asyncio
import logging
from decouple import config
from adk.api import Session
from agents.alpha_factory import alpha_factory
from agents.monitoring_agent import monitoring_agent
from agents.db_tools import db # Import the shared db instance

def setup_logging():
    # ... (logging setup remains the same)

async def run_alpha_factory():
    # ... (function remains the same)

async def run_monitoring_agent():
    # ... (function remains the same)

async def main():
    """
    Main function to run the Alpha Factory and the Monitoring Agent concurrently,
    while managing the database connection lifecycle.
    """
    setup_logging()
    
    # Connect to the database
    await db.connect()

    try:
        # Run the main application tasks
        await asyncio.gather(
            run_monitoring_agent(),
            run_alpha_factory()
        )
    finally:
        # Ensure the database connection is closed gracefully
        await db.close()
        logging.info("Database connection closed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSystem stopped by user.")
    except Exception as e:
        logging.error(f"Critical System Error: {e}", exc_info=True)
