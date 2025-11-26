import asyncio
import logging
from trading_bot.core.bot import Bot

def setup_logging():
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File Handler
    file_handler = logging.FileHandler('trading_bot.log')
    file_handler.setFormatter(log_formatter)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

if __name__ == "__main__":
    setup_logging()
    try:
        bot = Bot()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        logging.error(f"Critical System Error: {e}", exc_info=True)
