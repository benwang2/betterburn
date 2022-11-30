import requests
import disnake

from disnake.ext import commands
from disnake.ui import ActionRow

import os, my_secrets
my_secrets.load_env()

from cogs.presence import Presence
from cogs.guide import Guide
from cogs.leaderboard import Leaderboard
from cogs.fuzzy import Fuzzy


client = commands.InteractionBot(
    test_guilds=[863809747596607538],
    sync_commands_debug = True
)

invite_link = "https://discord.com/api/oauth2/authorize?client_id=704757052991602688&permissions=52288&scope=bot%20applications.commands"

SteamAppNewsUrl = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid=383980"
@client.slash_command(
    name="online",
    description="Counts how many players are playing Rivals of Aether."
)
async def online(inter):
    req = requests.get(url=SteamAppNewsUrl)
    data = req.json()
    if data.get("response"):
        if data["response"].get("player_count"):
            await inter.response.send_message("There are **"+str(data["response"]["player_count"])+"** people playing Rivals of Aether right now.")

@client.slash_command(
    name="invite",
    description="Get an invite link to add Betterburn to your own server."
)
async def invite(inter):
    actionRow: ActionRow = ActionRow()
    actionRow.add_button(label="Invite", url=invite_link)
    await inter.response.send_message(components=actionRow)

@client.event
async def on_command_error(ctx, error):
    pass

@client.event
async def on_ready():
    print("betterburn online, v2.00")
    client.add_cog(Presence(client))
    client.add_cog(Guide(client))
    client.add_cog(Fuzzy(client))
    client.add_cog(Leaderboard(client))

client.run(os.environ["DISCORD_TOKEN"])