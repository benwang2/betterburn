from discord.ext import tasks, commands

import db.session.utils
import db.cache.utils
import bridge

from config import Config

from steamboard import SteamLeaderboard


class MaidCog(commands.Cog, name="MaidCog"):
    def __init__(self, bot):
        self.bot = bot
        self.leaderboard = SteamLeaderboard(Config.app_id, Config.leaderboard_id)

        self.cull.start()
        self.update_cache.start()

    def cog_unload(self):
        self.cull.cancel()

    @tasks.loop(seconds=Config.session_duration)
    async def cull(self):
        bridge.cull_expired_linked_sessions()
        db.session.utils.cull_expired_sessions()

    @tasks.loop(seconds=Config.cache_update_interval)
    async def update_cache(self):
        self.leaderboard.update()

        db.cache.utils.clear_cache_table()
        db.cache.utils.bulk_insert_cache_from_list(self.leaderboard.to_list())
        db.cache.utils.update_metadata(len(self.leaderboard))
