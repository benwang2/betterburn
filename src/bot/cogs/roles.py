from discord.ext import tasks, commands

import db.session.utils
import db.cache.utils
import bridge

from config import Config

cfg = Config()


class Helper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        # self.cull.cancel()
        pass
