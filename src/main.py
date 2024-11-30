import asyncio
import threading

from api.api import start as start_fastapi
from bot.bot import start_bot
from db.database import init_db
import db.session.utils
import db.cache.utils

from steamboard.steamboard import SteamLeaderboard
from config import Config

cfg = Config()


# Start both the bot and the FastAPI server
def run():
    init_db()

    leaderboard = SteamLeaderboard(cfg.app_id, cfg.leaderboard_id, mute=False)
    leaderboard.update()

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
