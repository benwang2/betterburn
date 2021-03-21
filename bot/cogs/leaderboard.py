import os, time, random, requests
import discord, asyncio
from discord.ext import commands
from cogs import presence, fuzzy, leaderboard

client = commands.Bot(command_prefix="!",help_command=None)

__TOKEN = os.getenv("DISCORD_TOKEN")
__SERVERS_DRAG_PERM = os.getenv("SERVERS_DRAG_PERM")

@client.command()
@commands.has_role("Members")
async def drag(ctx, *args):
    if (str(ctx.guild.id) in __SERVERS_DRAG_PERM): # Custom Drag command
        if (ctx.author.voice and ctx.author.voice.channel):
            for moveme in ctx.message.mentions:
                if not moveme: continue
                role = discord.utils.get(ctx.channel.guild.roles, name='Members')
                if not role in moveme.roles or ctx.message.author.server_permissions.administrator:
                    if moveme.voice and moveme.voice.channel:
                        await moveme.move_to(ctx.author.voice.channel,reason="<@"+str(ctx.author.display_name)+"> used drag command.")
                        await ctx.message.add_reaction("✅")
                    else:
                        await ctx.send("<@"+str(moveme.id)+"> must join a voice channel.")
        else:
            await ctx.send("<@"+str(ctx.message.author.id)+"> must join a voice channel.")

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


client.run(__TOKEN)
