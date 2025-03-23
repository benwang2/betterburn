from discord.ext import commands
from config import Config


cfg = Config()


class Helper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        # self.cull.cancel()
        pass
