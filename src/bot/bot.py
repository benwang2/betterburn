from config import Config

import discord
from discord import app_commands
from api.utils import generate_link_url

import db.discord.utils
from db.session.utils import create_or_extend_session, end_session

from db.cache.utils import get_score_by_steam_id

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
    view = LinkView(link_url=link_url, on_cancel=lambda: end_session(session_id))

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
        unlink_user = lambda: db.discord.utils.unlink_user(discord_id)
        view = UnlinkView(unlink_user)
    else:
        embed = discord.Embed(
            title="Unlink Steam account.",
            description="Your Discord account is not linked to a Steam account.",
            color=discord.Color.red(),
        )

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@tree.command(
    name="check",
    description="Check information about a specific member.",
    guild=discord.Object(id=cfg.test_guild),
)
@app_commands.describe(member="The member you want to check")
async def check(interaction: discord.Interaction, member: discord.Member):
    """Handles the /check command."""
    embed = discord.Embed(
        title=f"Information about {member.display_name}", color=discord.Color.blue()
    )
    embed.add_field(
        name="Username", value=f"{member.name}#{member.discriminator}", inline=False
    )
    embed.add_field(name="ID", value=member.id, inline=False)
    embed.add_field(
        name="Joined Server",
        value=(
            member.joined_at.strftime("%Y-%m-%d %H:%M:%S")
            if member.joined_at
            else "Unknown"
        ),
        inline=False,
    )
    embed.add_field(
        name="Account Created",
        value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        inline=False,
    )

    member_steam_id = db.discord.utils.get_steam_id(member.id)

    if member_steam_id != None:
        embed.add_field(
            name="ELO", value=get_score_by_steam_id(member_steam_id), inline=False
        )
    embed.set_thumbnail(url=member.display_avatar.url)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=cfg.test_guild))
    print(f"Logged in as {client.user}")


async def start_bot():
    await client.start(TOKEN)
