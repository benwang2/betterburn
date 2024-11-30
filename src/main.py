import asyncio
import threading

from api.api import start as start_fastapi
from bot.bot import start_bot


# Start both the bot and the FastAPI server
def run():
    # Run FastAPI in a background thread
    fastapi_thread = threading.Thread(target=start_fastapi)
    fastapi_thread.start()

    # Run the bot in the main thread
    asyncio.run(start_bot())


if __name__ == "__main__":
    run()
