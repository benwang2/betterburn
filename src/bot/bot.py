from config import Config

import discord
from discord import app_commands
from db.session.utils import create_or_extend_session, get_session
from api.utils import generate_link_url

from .views import LinkView

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


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=cfg.test_guild))
    print(f"Logged in as {client.user}")


async def start_bot():
    await client.start(
        "NzExMDcxNzk5MzI4MTEyNjcx.G3R2h9.-TVAaUcZUYwlU9ELD00Pn0F8lVTv-DMnU2_DEU"
    )
