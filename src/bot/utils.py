"""
Utility functions for Discord bot operations.

This module provides helper functions for role assignment, verification,
and timestamp formatting used throughout the bot.
"""

from datetime import datetime

import discord

from ..db.cache.utils import last_updated_at
from .cogs.roles import RoleAssignmentResult, RoleCog


def relative_discord_timestamp(timestamp: str | int | float | None) -> str | None:
    """
    Convert a timestamp to a Discord relative timestamp string.

    Args:
        timestamp: A timestamp in various formats (ISO string, int, float, or None)

    Returns:
        A Discord relative timestamp string (e.g., "<t:1234567890:R>") or None
    """
    if timestamp is None:
        return None

    try:
        if isinstance(timestamp, str):
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return f"<t:{int(parsed.timestamp())}:R>"

        return f"<t:{int(timestamp)}:R>"
    except (TypeError, ValueError):
        return None


async def assign_roles_for_guild_ids(
    user_id: int, guild_ids: list[int], bot: discord.ext.commands.Bot, *, skip_guild_id: int | None = None
) -> None:
    """
    Assign roles to a user across multiple guilds.

    Fetches the user in each guild and assigns roles according to their rank.
    Skips guilds where the user is not a member or cannot be fetched.

    Args:
        user_id: The Discord user ID to assign roles for
        guild_ids: List of guild IDs to assign roles in
        bot: The Discord bot instance
        skip_guild_id: Optional guild ID to skip during role assignment
    """
    role_cog: RoleCog | None = bot.get_cog("RoleCog")
    if role_cog is None:
        return

    for guild_id in guild_ids:
        if skip_guild_id is not None and guild_id == skip_guild_id:
            continue

        guild = bot.get_guild(guild_id)
        if guild is None:
            continue

        member = guild.get_member(user_id)
        if member is None:
            try:
                member = await guild.fetch_member(user_id)
            except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                member = None

        if member is not None:
            await role_cog.assign_roles(member)


async def perform_verification(interaction: discord.Interaction) -> None:
    """
    Perform rank verification for a user who is already linked to Steam.

    This is the core verification logic that checks the user's rank and assigns roles.
    It assumes the user already has a Steam ID linked to their Discord account.

    Args:
        interaction: The Discord interaction (must already be deferred before calling)
    """
    role_cog: RoleCog = interaction.client.get_cog("RoleCog")
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

        leaderboard_timestamp = relative_discord_timestamp(result.updated_at)
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
