from config import Config

import discord
from discord.ext.commands import Bot
from discord import app_commands
from api.utils import generate_link_url

import db.cache
import db.cache.utils
import db.discord.utils
import db.cache.utils
from db.session.utils import create_or_extend_session, end_session

from bridge import create_linked_session

from .views import LinkView, UnlinkView

from .cogs.maid import MaidCog
from .cogs.roles import RoleCog

TOKEN = Config.discord_token

intents = discord.Intents.default()
client: Bot = Bot(command_prefix="", intents=intents)
# tree = app_commands.CommandTree(client)


@client.tree.command(
    name="link",
    description="Link your Discord account to a Steam account.",
    guilds=[discord.Object(id=guild_id) for guild_id in Config.test_guild],
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

    async def handler(steam_id):
        try:
            message = await interaction.original_response()
            embed = discord.Embed(
                title="You have linked your Discord account. Run `/verify` to verify your rank.",
                description=f"Your account was linked to SteamID: {steam_id}",
                color=discord.Color.green(),
            )
            await message.edit(embed=embed, view=None)
        except Exception as e:
            print(f"Failed to update message: {e}")

    async def event(*args, **kwargs):
        client.loop.create_task(handler(*args, **kwargs))

    linked_session = create_linked_session(session_id=session_id, discord_id=discord_id)
    linked_session.setEventHandler(event)


@client.tree.command(
    name="unlink",
    description="Unlinks any existing steam account.",
    guilds=[discord.Object(id=guild_id) for guild_id in Config.test_guild],
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


@client.tree.command(
    name="verify",
    description="Verify your rank and receive the respective role.",
    guilds=[discord.Object(id=guild_id) for guild_id in Config.test_guild],
)
# @app_commands.describe(score="The score you want to test")
async def verify(
    interaction: discord.Interaction,
    score: discord.app_commands.Range[int, 0, 1600] = None,
):
    discord_id = interaction.user.id

    embed: discord.Embed = None
    view: discord.ui.View = None

    if (steam_id := db.discord.utils.get_steam_id(discord_id)) != None:
        score = db.cache.utils.get_score_by_steam_id(steam_id)
        rank: str = "Stone"

        if score < 500:
            rank = "Stone"
            color = discord.Color.dark_gray()
        elif score >= 500 and score < 700:
            rank = "Bronze"
            color = discord.Color.dark_orange()
        elif score >= 700 and score < 800:
            rank = "Silver"
            color = discord.Color.light_gray()
        elif score >= 800 and score < 1100:
            rank = "Gold"
            color = discord.Color.gold()
        elif score >= 1100 and score < 1300:
            rank = "Platinum"
            color = discord.Color.lighter_gray()
        elif score >= 1300 and score < 1500:
            rank = "Diamond"
            color = discord.Color.blue()
        elif score >= 1500:
            rank = "Master"
            color = discord.Color.brand_green()

        file = discord.File(
            f"./src/img/{rank.lower()}.png", filename=f"{rank.lower()}.png"
        )
        embed = discord.Embed(
            title="Your rank has been verified.",
            description=f"{rank} - {score}",
            color=color,
        )

        ranks_to_remove: list = [key.capitalize() for key in cfg.roles.keys()]
        ranks_to_remove.remove(rank)

        roles_to_remove = tuple(
            discord.utils.get(interaction.guild.roles, name=name)
            for name in tuple(ranks_to_remove)
        )
        role = discord.utils.get(interaction.guild.roles, name=rank)

        owned_roles = [role.name for role in interaction.user.roles]
        if rank not in owned_roles:
            await interaction.user.remove_roles(*roles_to_remove)
            await interaction.user.add_roles(role)

        embed.set_image(url=f"attachment://{rank.lower()}.png")

        await interaction.response.send_message(
            embed=embed, file=file, view=view, ephemeral=True
        )
    else:
        embed = discord.Embed(
            title="Link a Steam account.",
            description="Your Discord account is not linked to a Steam account.",
            color=discord.Color.red(),
        )

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@client.tree.command(
    name="check",
    description="Check information about a specific member.",
    guilds=[discord.Object(id=guild_id) for guild_id in Config.test_guild],
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

    if member_steam_id is not None:
        embed.add_field(
            name="ELO",
            value=db.cache.utils.get_score_by_steam_id(member_steam_id),
            inline=False,
        )
    embed.set_thumbnail(url=member.display_avatar.url)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@client.tree.command(
    name="status",
    description="Check the status of the database.",
    guilds=[discord.Object(id=guild_id) for guild_id in Config.test_guild],
)
async def status(interaction: discord.Interaction):
    """Handles the /status command."""

    embed: discord.Embed = discord.Embed(
        title="Steamboard Status",
        color=discord.Color.green(),
    )

    last_updated = db.cache.utils.last_updated_at()
    last_updated_ut = f"<t:{int(last_updated.timestamp())}:F>"
    embed.add_field(name="Last updated", value=last_updated_ut, inline=False)

    player_count = db.cache.utils.get_player_count()
    embed.add_field(
        name="Number of Players",
        value=player_count,
        inline=False,
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)


@client.event
async def on_ready():

    await client.add_cog(MaidCog(client))
    await client.add_cog(RoleCog(client))

    for guild_id in Config.test_guild:
        try:
            await client.tree.sync(guild=discord.Object(id=guild_id))
        except discord.Forbidden as ex:
            # Handle forbidden errors (e.g., bot lacks permissions)
            print(
                f"Discord bot lacks permissions to sync commands to guild_id = {guild_id}"
            )
            print(ex)
        except Exception as ex:
            print(ex)

    await client.tree.sync()

    print(f"Logged in as {client.user}")


async def start_bot():
    await client.start(TOKEN)
