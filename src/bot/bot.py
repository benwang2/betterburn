from config import Config

import discord
from discord.ext.commands import Bot
from discord import app_commands
from api.utils import generate_link_url

from db.cache.utils import (
    last_updated_at,
    get_player_count,
    get_rank_data_by_steam_id,
    get_rank_from_row,
)
from db.discord.utils import get_steam_id, unlink_user, get_role_id_for_rank
from db.session.utils import create_or_extend_session, end_session

from bridge import create_linked_session

from .views import LinkView, UnlinkView

from .cogs.maid import MaidCog
from .cogs.roles import RoleCog

from custom_logger import CustomLogger as Logger

TOKEN = Config.discord_token

intents = discord.Intents.default()
client: Bot = Bot(command_prefix="", intents=intents)
logger = Logger("discord")
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
            logger.info(f'Linked Discord user <name="{interaction.user.name}" id={discord_id}> to SteamID = {steam_id}')

            embed = discord.Embed(
                title="You have linked your Discord account. Run `/verify` to verify your rank.",
                description=f"Your account was linked to SteamID: {steam_id}",
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
            (rank, rank_num, score, role_id) = message
            role: discord.Role = discord.utils.get(interaction.guild.roles, id=role_id)
            file = discord.File(f"./src/img/{rank.lower()}.png", filename=f"{rank.lower()}.png")
            embed = discord.Embed(
                title="Your rank has been verified.",
                description=f"**{rank}** - `{score}` - #{rank_num}",
                color=role.color,
            )
            embed.set_image(url=f"attachment://{rank.lower()}.png")

            last_updated = last_updated_at()
            if last_updated is not None:
                last_updated_text = f"<t:{int(last_updated)}:R>"
                embed.add_field(name="Database last updated", value=last_updated_text, inline=False)

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
    ranked_data = None

    if member_steam_id is not None:
        ranked_data = get_rank_data_by_steam_id(member_steam_id)

    if ranked_data is not None:
        rank = get_rank_from_row(ranked_data)
        role: discord.Role = discord.utils.get(member.guild.roles, id=get_role_id_for_rank(member.guild.id, rank))
        embed.add_field(
            name="ELO",
            value=ranked_data.score,
            inline=False,
        )
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
        title="Steamboard Status",
        color=discord.Color.green(),
    )

    last_updated = last_updated_at()
    if last_updated is not None:
        last_updated_text = f"<t:{int(last_updated)}:R>"
        embed.add_field(name="Last updated", value=last_updated_text, inline=False)

    player_count = get_player_count()
    embed.add_field(
        name="Number of Players",
        value=player_count,
        inline=False,
    )

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
