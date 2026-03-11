from datetime import datetime

import discord
from discord import app_commands
from discord.ext.commands import Bot

from ..api.utils import generate_link_url
from ..bridge import create_linked_session
from ..config import Config
from ..custom_logger import CustomLogger as Logger
from ..db.cache.utils import (
    get_player_count,
    get_rank_data_by_steam_id,
    get_rank_from_row,
    get_rank_from_values,
    last_updated_at,
)
from ..db.discord.utils import get_role_id_for_rank, get_steam_id, unlink_user
from ..db.session.utils import create_or_extend_session, end_session
from ..leaderboard_api import (
    LeaderboardApiBadRequestError,
    LeaderboardApiNotFoundError,
    LeaderboardApiUnavailableError,
    is_leaderboard_api_enabled,
)
from ..leaderboard_api import (
    client as leaderboard_api,
)
from .cogs.maid import MaidCog
from .cogs.roles import RoleAssignmentResult, RoleCog
from .views import LinkView, UnlinkView

TOKEN = Config.discord_token

intents = discord.Intents.default()
client: Bot = Bot(command_prefix="", intents=intents)
logger = Logger("discord")
# tree = app_commands.CommandTree(client)


def _relative_discord_timestamp(timestamp: str | int | float | None) -> str | None:
    if timestamp is None:
        return None

    try:
        if isinstance(timestamp, str):
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return f"<t:{int(parsed.timestamp())}:R>"

        return f"<t:{int(timestamp)}:R>"
    except (TypeError, ValueError):
        return None


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

    async def handler(steam_id, mapping_message: str | None = None):
        try:
            message = await interaction.original_response()
            logger.info(f'Linked Discord user <name="{interaction.user.name}" id={discord_id}> to SteamID = {steam_id}')

            description = f"Your account was linked to SteamID: {steam_id}"
            if mapping_message:
                description = f"{description}\n\n{mapping_message}"

            embed = discord.Embed(
                title="You have linked your Discord account. Run `/verify` to verify your rank.",
                description=description,
                color=discord.Color.green(),
            )

            await message.edit(embed=embed, view=None)
        except Exception as e:
            logger.error(str(e))

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
    await interaction.response.defer(ephemeral=True)
    discord_id = interaction.user.id

    embed: discord.Embed = None
    view: discord.ui.View = None

    if get_steam_id(discord_id) is not None:
        embed = discord.Embed(
            title="Unlink Steam account.",
            description="Click the 'Confirm' button below to unlink your account.",
            color=discord.Color.blurple(),
        )

        async def unlink_action():
            await unlink_user(discord_id)
            logger.info(f'Unlinked Discord user <name="{interaction.user.name}" id={discord_id}>')

        view = UnlinkView(unlink_action)
        await interaction.followup.send(embed=embed, view=view)
    else:
        embed = discord.Embed(
            title="Unlink Steam account.",
            description="Your Discord account is not linked to a Steam account.",
            color=discord.Color.red(),
        )

        await interaction.followup.send(embed=embed)


@client.tree.command(
    name="verify",
    description="Verify your rank and receive the respective role.",
    guilds=[discord.Object(id=guild_id) for guild_id in Config.test_guild],
)
# @app_commands.describe(score="The score you want to test")
async def verify(
    interaction: discord.Interaction,
):
    await interaction.response.defer(thinking=False)
    embed: discord.Embed = None

    if get_steam_id(interaction.user.id) is not None:
        role_cog: RoleCog = client.get_cog("RoleCog")
        (succ, message) = await role_cog.assign_roles(interaction.user)
        if succ:
            result: RoleAssignmentResult = message
            rank = result.rank.name
            role: discord.Role = discord.utils.get(interaction.guild.roles, id=result.role_id)
            file = discord.File(f"./src/img/{rank.lower()}.png", filename=f"{rank.lower()}.png")
            embed = discord.Embed(
                title="Your rank has been verified.",
                description=f"**{rank}** - `{result.score}` - #{result.position}",
                color=role.color,
            )
            embed.set_image(url=f"attachment://{rank.lower()}.png")

            leaderboard_timestamp = _relative_discord_timestamp(result.updated_at)
            if leaderboard_timestamp is not None:
                field_name = "Leaderboard updated" if result.source == "leaderboard_api" else "Database last updated"
                embed.add_field(name=field_name, value=leaderboard_timestamp, inline=False)

            await interaction.followup.send(embed=embed, file=file)
        else:
            embed = discord.Embed(
                title="An error occurred.",
                description=message,
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed)
    else:
        embed = discord.Embed(
            title="Link a Steam account.",
            description="Your Discord account is not linked to a Steam account. Run the `/link` command to link your steam account.",
            color=discord.Color.red(),
        )

        await interaction.followup.send(embed=embed)


@client.tree.command(
    name="check",
    description="Check information about a specific member.",
    guilds=[discord.Object(id=guild_id) for guild_id in Config.test_guild],
)
@app_commands.describe(member="The member you want to check")
@app_commands.check(lambda interaction: interaction.user.id == 154046172254830592)
async def check(interaction: discord.Interaction, member: discord.Member):
    """Handles the /check command."""
    embed = discord.Embed(title=f"Information about {member.display_name}", color=discord.Color.blue())
    embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}", inline=False)
    embed.add_field(name="ID", value=member.id, inline=False)
    embed.add_field(
        name="Joined Server",
        value=(member.joined_at.strftime("%Y-%m-%d %H:%M:%S") if member.joined_at else "Unknown"),
        inline=False,
    )
    embed.add_field(
        name="Account Created",
        value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        inline=False,
    )

    member_steam_id = get_steam_id(member.id)

    if member_steam_id is not None:
        if is_leaderboard_api_enabled():
            try:
                standing = await leaderboard_api.get_standing_async(member_steam_id)
                rank = get_rank_from_values(standing.stat_value, standing.position)
                role_id = get_role_id_for_rank(member.guild.id, rank)
                role: discord.Role | None = discord.utils.get(member.guild.roles, id=role_id) if role_id else None
                embed.add_field(name="ELO", value=standing.stat_value, inline=False)
                embed.add_field(name="Leaderboard Position", value=f"#{standing.position}", inline=False)

                leaderboard_timestamp = _relative_discord_timestamp(standing.timestamp)
                if leaderboard_timestamp is not None:
                    embed.add_field(name="Leaderboard updated", value=leaderboard_timestamp, inline=False)

                if role is not None:
                    embed.color = role.color
            except LeaderboardApiNotFoundError:
                embed.add_field(name="Leaderboard", value="No leaderboard data found.", inline=False)
            except LeaderboardApiBadRequestError as exc:
                embed.add_field(name="Leaderboard", value=str(exc), inline=False)
            except LeaderboardApiUnavailableError:
                embed.add_field(name="Leaderboard", value="Leaderboard service is currently unavailable.", inline=False)
        else:
            ranked_data = get_rank_data_by_steam_id(member_steam_id)
            if ranked_data is not None:
                rank = get_rank_from_row(ranked_data)
                role_id = get_role_id_for_rank(member.guild.id, rank)
                role: discord.Role | None = discord.utils.get(member.guild.roles, id=role_id) if role_id else None
                embed.add_field(name="ELO", value=ranked_data.score, inline=False)
                embed.add_field(name="Leaderboard Position", value=f"#{ranked_data.rank}", inline=False)

                last_updated = _relative_discord_timestamp(last_updated_at())
                if last_updated is not None:
                    embed.add_field(name="Database last updated", value=last_updated, inline=False)

                if role is not None:
                    embed.color = role.color

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
        title="Leaderboard API Status" if is_leaderboard_api_enabled() else "Steamboard Status",
        color=discord.Color.blurple(),
    )

    if is_leaderboard_api_enabled():
        embed.add_field(name="Base URL", value=Config.leaderboard_api_base_url, inline=False)

        try:
            health = await leaderboard_api.get_health_async()
            embed.add_field(name="Service Status", value=str(health.get("status", "unknown")), inline=False)
            embed.add_field(name="Authenticated", value=str(health.get("authenticated", False)), inline=False)
            embed.color = discord.Color.green()
        except LeaderboardApiUnavailableError:
            embed.add_field(name="Service Status", value="unavailable", inline=False)
            embed.color = discord.Color.red()
    else:
        last_updated = last_updated_at()
        if last_updated is not None:
            embed.add_field(name="Last updated", value=f"<t:{int(last_updated)}:R>", inline=False)

        embed.add_field(name="Number of Players", value=get_player_count(), inline=False)
        embed.color = discord.Color.green()

    await interaction.response.send_message(embed=embed, ephemeral=True)


@client.event
async def on_ready():
    guilds = [guild.id for guild in client.guilds]

    for guild_id in guilds:
        if guild_id not in Config.test_guild:
            server = client.get_guild(guild_id)
            client_mbr = server.get_member(client.user.id)
            logger.info(f"Betterburn joined <name={server.name} id={guild_id}> on {client_mbr.joined_at}")
            await server.leave()

    await client.add_cog(MaidCog(client))
    await client.add_cog(RoleCog(client))

    for guild_id in Config.test_guild:
        try:
            await client.tree.sync(guild=discord.Object(id=guild_id))
        except discord.Forbidden:
            # Handle forbidden errors (e.g., bot lacks permissions)
            logger.error(f"Discord bot lacks permissions to sync commands to guild_id = {guild_id}")
        except Exception as e:
            logger.error(str(e))

    await client.tree.sync()

    print(f"Logged in as {client.user}")


async def start_bot():
    await client.start(TOKEN)
