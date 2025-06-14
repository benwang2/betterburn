from discord.ext import commands, tasks

from ... import bridge
from ...config import Config
from ...custom_logger import CustomLogger as Logger
from ...db.cache import utils as cache_utils
from ...db.session import utils as session_utils
from ...steamboard import SteamLeaderboard


class MaidCog(commands.Cog, name="MaidCog"):
    def __init__(self, bot):
        self.logger = Logger("maid")
        self.bot = bot
        self.leaderboard = SteamLeaderboard(Config.app_id, Config.leaderboard_id)

        self.cull.start()
        self.update_cache.start()

    def cog_unload(self):
        self.cull.cancel()

    @tasks.loop(seconds=Config.session_duration)
    async def cull(self):
        culled_linking_sessions = bridge.cull_expired_linked_sessions()
        culled_sessions = session_utils.cull_expired_sessions()
        self.logger.info(f"Culled {culled_linking_sessions} linked sessions.")
        self.logger.info(f"Culled {culled_sessions} sessions.")

    @tasks.loop(seconds=Config.cache_update_interval)
    async def update_cache(self):
        self.leaderboard.update()

        cache_utils.clear_cache_table()
        cache_utils.bulk_insert_cache_from_list(self.leaderboard.to_list())
        cache_utils.update_metadata(len(self.leaderboard))

        self.logger.info("Updated database cache.")
