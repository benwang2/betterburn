import asyncio
import sys
import threading

from .api.api import start as start_fastapi
from .bot.bot import start_bot
from .db.database import init_db

import traceback
from custom_logger import CustomLogger as Logger

logger = Logger("root")


def catch_exceptions(*exception_info):
    text = "".join(traceback.format_exception(*exception_info))
    if "KeyboardInterrupt" in text:
        pass
    logger.error((f"Unhandled exception occurred: {text}"))


sys.excepthook = catch_exceptions


# Start both the bot and the FastAPI server
def run():
    init_db()

    # Run FastAPI in a background thread
    fastapi_thread = threading.Thread(target=start_fastapi)
    fastapi_thread.start()

    # Run the bot in the main thread
    asyncio.run(start_bot())


if __name__ == "__main__":
    run()
