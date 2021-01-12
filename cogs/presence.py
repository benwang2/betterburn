import discord, random
from discord import client
from discord.ext import tasks, commands

activities = [
    'Grinding pity flips',
    'Practicing shine upstrongs',
    'Smurfing on ranked',
    'Down-smashing on casual!',
    'Getting edgeguarded by Kragg',
    'Offstage without an airdodge',
    'Spamming my "neutral" tool'
]

class cog(commands.Cog):
    def __init__(self, bot):
        self.index = random.randrange(0, len(activities))
        self.bot = bot
        self.setPresence.start()

    async def cog_unload(self):
        self.setPresence.cancel()

    @tasks.loop(seconds=60*5)
    async def setPresence(self):
        self.index += 1
        if (self.index>=len(activities)):
            self.index = 0
        await self.bot.change_presence(activity=discord.Game(activities[self.index]+" | !betterburn"))

