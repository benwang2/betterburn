from discord.ext import commands, tasks

from ... import bridge
from ...config import Config
from ...custom_logger import CustomLogger as Logger
from ...db.session import utils as session_utils


class MaidCog(commands.Cog, name="MaidCog"):
    def __init__(self, bot):
        self.logger = Logger("maid")
        self.bot = bot

        self.cull.start()

    async def cog_unload(self):
        self.cull.cancel()

    @tasks.loop(seconds=Config.session_duration)
    async def cull(self):
        culled_linking_sessions = bridge.cull_expired_linked_sessions()
        culled_sessions = session_utils.cull_expired_sessions()
        self.logger.info(f"Culled {culled_linking_sessions} linked sessions.")
        self.logger.info(f"Culled {culled_sessions} sessions.")
