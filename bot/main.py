import os, time, random, requests
import disnake, asyncio
from disnake.ext import commands

from cogs.presence import Presence
from cogs.guide import Guide
from cogs.leaderboard import Leaderboard

client = commands.InteractionBot(
    test_guilds=[12345],
    # sync_commands=False
    sync_commands_debug = True
)

SteamAppNewsUrl = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid=383980"
@client.slash_command(
    name="online",
    description="Counts how many players are playing Rivals of Aether."
)
async def online(ctx):
    req = requests.get(url=SteamAppNewsUrl)
    data = req.json()
    if data.get("response"):
        if data["response"].get("player_count"):
            await ctx.response.send_message("There are **"+str(data["response"]["player_count"])+"** people playing Rivals of Aether right now.")

@client.event
async def on_command_error(ctx, error):
    pass

@client.event
async def on_ready():
    print("betterburn online, v2.00")
    client.add_cog(Presence(client))
    client.add_cog(Guide(client))
    # client.add_cog(fuzzy.Fuzzy(client))
    client.add_cog(Leaderboard(client))

client.run(os.getenv("DISCORD_TOKEN"))