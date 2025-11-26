import asyncio
import logging
from trading_bot.core.bot import Bot

if __name__ == "__main__":
    try:
        bot = Bot()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        # logging.error here might miss if setup failed
        print(f"Critical System Error: {e}")