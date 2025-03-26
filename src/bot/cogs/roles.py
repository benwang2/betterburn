import discord
from discord.ext import commands

import db.session.utils
import db.cache.utils

from config import Config

cfg = Config()


class RoleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        # self.cull.cancel()
        pass
