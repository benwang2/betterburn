import asyncio
import threading

from api.api import start as start_fastapi
from bot.bot import start_bot
from db.database import init_db
import db.session.utils
import db.cache.utils

from config import Config
from steamboard import leaderboard

cfg = Config()


# Start both the bot and the FastAPI server
def run():
    init_db()

    db.cache.utils.clear_cache_table()
    db.cache.utils.bulk_insert_cache_from_list(leaderboard.to_list())

    db.session.utils.cull_expired_sessions()

    # Run FastAPI in a background thread
    fastapi_thread = threading.Thread(target=start_fastapi)
    fastapi_thread.start()

    # Run the bot in the main thread
    asyncio.run(start_bot())


if __name__ == "__main__":
    run()
