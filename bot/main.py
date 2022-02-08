import os, time, random, requests, config
import discord, asyncio
from discord.ext import commands
from cogs import presence, fuzzy, leaderboard

client = commands.Bot(command_prefix="!",help_command=None)

SteamAppNewsUrl = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid=383980"
@client.command(name="online")
async def online(ctx):
    req = requests.get(url=SteamAppNewsUrl)
    data = req.json()
    if data.get("response"):
        if data["response"].get("player_count"):
            await ctx.send("There are **"+str(data["response"]["player_count"])+"** people playing Rivals of Aether right now.")

@client.event
async def on_command_error(ctx, error):
    pass

@client.event
async def on_ready():
    print("betterburn online, v2.00")
    client.add_cog(presence.cog(client))
    client.add_cog(fuzzy.cog(client))
    client.add_cog(leaderboard.cog(client))

client.run(config.DISCORD_TOKEN)