import disnake, random
from disnake import client
from disnake.ext import tasks, commands

activities = [
    'Grinding pity flips',
    'Practicing shine upstrongs',
    'Smurfing on ranked',
    'Down-smashing on casual!',
    'Getting edgeguarded by Kragg',
    'Offstage without an airdodge',
    'Spamming my "neutral" tool'
]

class Presence(commands.Cog):
    def __init__(self, bot):
        self.index = random.randrange(0, len(activities))
        self.bot = bot
        

    async def cog_unload(self):
        self.setPresence.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        self.setPresence.start()

    @tasks.loop(seconds=60*5)
    async def setPresence(self):
        self.index += 1
        if (self.index>=len(activities)):
            self.index = 0
        await self.bot.change_presence(activity=disnake.Game(activities[self.index]+" | !betterburn"))