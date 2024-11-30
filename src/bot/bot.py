from config import Config

import discord
from discord import app_commands
from api.utils import generate_link_url

import db.discord
import db.discord.utils
from db.session.utils import create_or_extend_session

from .views import LinkView, UnlinkView

cfg = Config()
TOKEN = cfg.discord_token

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@tree.command(
    name="link",
    description="Link your Discord account to a Steam account.",
    guild=discord.Object(id=cfg.test_guild),
)
async def link(interaction: discord.Interaction):
    discord_id = interaction.user.id
    session_id = create_or_extend_session(discord_id)
    link_url = generate_link_url(session_id)

    embed = discord.Embed(
        title="Link your steam account.",
        description="Click the 'Authenticate' button below to link your account.",
        color=discord.Color.blue(),
    )
    view = LinkView(link_url)

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@tree.command(
    name="unlink",
    description="Unlinks any existing steam account.",
    guild=discord.Object(id=cfg.test_guild),
)
async def unlink(interaction: discord.Interaction):
    discord_id = interaction.user.id

    embed: discord.Embed = None
    view: discord.ui.View = None

    if db.discord.utils.get_steam_id(discord_id) != None:
        embed = discord.Embed(
            title="Unlink Steam account.",
            description="Click the 'Confirm' button below to unlink your account.",
            color=discord.Color.blurple(),
        )
        view = UnlinkView()
    else:
        embed = discord.Embed(
            title="Unlink Steam account.",
            description="Your Discord account is not linked to a Steam account.",
            color=discord.Color.red(),
        )

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=cfg.test_guild))
    print(f"Logged in as {client.user}")


async def start_bot():
    await client.start(
        "NzExMDcxNzk5MzI4MTEyNjcx.G3R2h9.-TVAaUcZUYwlU9ELD00Pn0F8lVTv-DMnU2_DEU"
    )
