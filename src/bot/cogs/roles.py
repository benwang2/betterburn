from dataclasses import dataclass
from typing import Any, cast

import discord
from discord import app_commands
from discord.ext import commands

from ...config import Config
from ...constants import Colors, Rank, RoleDoctorOption
from ...custom_logger import CustomLogger as Logger
from ...db.cache.utils import get_rank_data_by_steam_id, get_rank_from_row, get_rank_from_values, last_updated_at
from ...db.discord.utils import (
    get_role_id_for_rank,
    get_roles_for_guild,
    get_steam_id,
    set_role_id_for_rank,
)
from ...leaderboard_api import (
    LeaderboardApiBadRequestError,
    LeaderboardApiNotFoundError,
    LeaderboardApiUnavailableError,
    is_leaderboard_api_enabled,
)
from ...leaderboard_api import (
    client as leaderboard_api,
)


@dataclass(frozen=True)
class RoleAssignmentResult:
    rank: Rank
    role_id: int
    score: int
    position: int
    updated_at: Any = None
    source: str = "steamboard"


class RoleCog(commands.Cog, name="RoleCog"):
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger("rolecog")
        self.leaderboard_api = leaderboard_api

    async def assign_roles(self, member: discord.Member) -> tuple[bool, object]:
        guild_id = member.guild.id

        steam_id = get_steam_id(member.id)

        if steam_id is None:
            return (False, f"No SteamID is linked to DiscordID {member.id}")

        if is_leaderboard_api_enabled():
            try:
                standing = await self.leaderboard_api.get_standing_async(steam_id)
            except LeaderboardApiNotFoundError:
                return (False, f"Couldn't find leaderboard data for SteamID {steam_id}")
            except LeaderboardApiBadRequestError as exc:
                return (False, str(exc))
            except LeaderboardApiUnavailableError:
                return (False, "Leaderboard service is currently unavailable. Please try again later.")

            rank = get_rank_from_values(standing.stat_value, standing.position)
            score = standing.stat_value
            position = standing.position
            updated_at = standing.timestamp
            source = "leaderboard_api"
        else:
            rank_data = get_rank_data_by_steam_id(steam_id)
            if rank_data is None:
                return (False, f"Couldn't find rank for SteamID {steam_id}")

            rank = get_rank_from_row(rank_data)
            score = cast(int, rank_data.score)
            position = cast(int, rank_data.rank)
            updated_at = last_updated_at()
            source = "steamboard"

        role_id = get_role_id_for_rank(guild_id, rank)

        if role_id:
            roles = get_roles_for_guild(guild_id)
            role_ids_to_remove = [val for val in roles.values() if val != role_id]
            roles_to_remove = tuple(
                role
                for role in (discord.utils.get(member.guild.roles, id=val) for val in role_ids_to_remove)
                if role is not None
            )
            target_role = discord.utils.get(member.guild.roles, id=role_id)

            if target_role is None:
                return (False, f"Configured role for rank {rank.name} no longer exists in this server.")

            owned_roles = [role.name for role in member.roles]
            if rank.name not in owned_roles:
                await member.add_roles(target_role)

            self.logger.info(
                f'Assigned role <name="{target_role.name}" id={role_id}> for rank {rank.name} to <name="{member.name}" id={member.id}>'
            )

            if roles_to_remove:
                await member.remove_roles(*roles_to_remove)

            return (
                True,
                RoleAssignmentResult(
                    rank=rank,
                    role_id=role_id,
                    score=score,
                    position=position,
                    updated_at=updated_at,
                    source=source,
                ),
            )

        return (False, f"No role is assigned to rank {rank.name}")

    @app_commands.command(name="roledoctor", description="Diagnose roles.")
    @app_commands.describe(option="Doctor option to run.")
    @app_commands.guilds(*[discord.Object(id=guild_id) for guild_id in Config.test_guild])
    async def roledoctor(self, interaction: discord.Interaction, option: RoleDoctorOption):
        # Allow the configured user ID or server administrators to run this command.
        allowed_user_id = Config.role_doctor_user_id
        try:
            is_admin = interaction.user.guild_permissions.administrator
        except Exception:
            is_admin = False

        print(allowed_user_id, interaction.user.id, is_admin)

        if not is_admin and (allowed_user_id is None or interaction.user.id != allowed_user_id):
            await interaction.response.send_message("You don't have permission to run this command.", ephemeral=True)
            return

        await interaction.response.defer()
        if option == RoleDoctorOption.check:
            roles = get_roles_for_guild(interaction.guild_id) or {}
            embed = discord.Embed(title="Rank to Role mapping")
            for rank in Rank:
                role_id = roles.get(rank.name)
                if role_id:
                    embed.add_field(name=rank.name, value=f"<@&{role_id}>")
                else:
                    embed.add_field(name=rank.name, value="Unmapped")
            await interaction.followup.send(embed=embed)
        elif option == RoleDoctorOption.test:
            pass
        elif option == RoleDoctorOption.auto:
            if interaction.guild is None:
                await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
                return

            guild = interaction.guild
            updated: list[str] = []
            already: list[str] = []
            missing: list[str] = []

            for rank in Rank:
                # find a role in the guild whose name matches the rank name (case-insensitive)
                match = discord.utils.find(lambda r: r.name.lower() == rank.name.lower(), guild.roles)
                if match:
                    succ = set_role_id_for_rank(guild.id, match.id, rank)
                    if succ:
                        updated.append(f"{rank.name} -> <@&{match.id}>")
                    else:
                        already.append(f"{rank.name} -> <@&{match.id}>")
                else:
                    # try to create the role using the same logic as scripts/create_rank_roles.py
                    try:
                        role_color = discord.Color(Colors[rank.name].value)
                    except Exception:
                        role_color = discord.Color.default()

                    try:
                        created = await guild.create_role(
                            name=rank.name,
                            color=role_color,
                            reason="Auto-created Betterburn rank role",
                        )
                    except discord.Forbidden:
                        missing.append(f"{rank.name} (no permission to create)")
                        continue
                    except Exception as exc:
                        missing.append(f"{rank.name} (create failed: {exc})")
                        continue

                    succ = set_role_id_for_rank(guild.id, created.id, rank)
                    if succ:
                        updated.append(f"{rank.name} -> <@&{created.id}> (created)")
                    else:
                        already.append(f"{rank.name} -> <@&{created.id}> (created)")

            embed = discord.Embed(title="RoleDoctor Auto-Assign Results")
            if updated:
                embed.add_field(name="Assigned", value="\n".join(updated), inline=False)
            if already:
                embed.add_field(name="Already Configured", value="\n".join(already), inline=False)
            if missing:
                embed.add_field(name="Not Found", value=", ".join(missing), inline=False)

            await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="config",
        description="Configure roles for your server.",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(rank="Rank to pair to role.", role="Role to pair to rank.")
    @app_commands.guilds(*[discord.Object(id=guild_id) for guild_id in Config.test_guild])
    async def configure(self, interaction: discord.Interaction, rank: Rank, role: discord.Role):
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        succ = set_role_id_for_rank(interaction.guild.id, role.id, rank)

        embed: discord.Embed

        if succ:
            embed = discord.Embed(
                title="Configuration complete",
                description=f"Assigned role {role.mention} to {rank.name}.",
                color=discord.Color.green(),
            )
        else:
            embed = discord.Embed(
                title="Configuration unsuccessful",
                description=f"Role {role.mention} is already assigned to {rank.name}.",
                color=discord.Color.red(),
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def cog_unload(self):
        # self.cull.cancel()
        pass
