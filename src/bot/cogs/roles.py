import discord
from discord import app_commands
from discord.ext import commands

from db.cache.utils import get_rank_data_by_steam_id, get_rank_from_row
from db.discord.utils import (
    get_role_id_for_rank,
    get_roles_for_guild,
    set_role_id_for_rank,
    get_steam_id,
)

from constants import Rank, RoleDoctorOption
from config import Config

from custom_logger import CustomLogger as Logger


class RoleCog(commands.Cog, name="RoleCog"):
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger("rolecog")

    async def assign_role(self, member: discord.Member) -> tuple[bool, object]:
        guild_id = member.guild.id

        steam_id = get_steam_id(member.id)

        if steam_id is None:
            return (False, f"No SteamID is linked to DiscordID {member.id}")

        rank_data = get_rank_data_by_steam_id(steam_id)

        if rank_data is None:
            return (False, f"Couldn't find rank for SteamID {steam_id}")

        rank = get_rank_from_row(rank_data)
        role_id = get_role_id_for_rank(guild_id, rank)

        if role_id:
            roles = get_roles_for_guild(guild_id)
            role_ids_to_remove = [val for val in roles.values() if val != role_id]
            roles_to_remove = tuple(
                discord.utils.get(member.guild.roles, id=val)
                for val in role_ids_to_remove
            )

            owned_roles = [role.name for role in member.roles]
            if rank.name not in owned_roles:
                await member.add_roles(
                    discord.utils.get(member.guild.roles, id=role_id)
                )

            self.logger.info(
                f'Assigned role <name="{discord.utils.get(member.guild.roles, id=role_id).name}" id={role_id}> for rank {rank.name} to <name="{member.name}" id={member.id}>'
            )

            await member.remove_roles(*roles_to_remove)
            return (True, (rank.name, rank_data.score))

        return (False, f"No role is assigned to rank {rank.name}")

    @app_commands.command(name="roledoctor", description="Diagnose roles.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(option="Doctor option to run.")
    @app_commands.guilds(
        *[discord.Object(id=guild_id) for guild_id in Config.test_guild]
    )
    async def roledoctor(
        self, interaction: discord.Interaction, option: RoleDoctorOption
    ):
        await interaction.response.defer()
        if option == RoleDoctorOption.check:
            roles = get_roles_for_guild(interaction.guild_id) or {}
            embed = discord.Embed(title="Rank to Role mapping")
            for rank in Rank:
                if roles[rank.name]:
                    embed.add_field(name=rank.name, value=f"<@&{roles[rank.name]}>")
                else:
                    embed.add_field(name=rank.name, value=f"Unmapped")
            await interaction.followup.send(embed=embed)
        elif option == RoleDoctorOption.test:
            pass

    @app_commands.command(
        name="config",
        description="Configure roles for your server.",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(rank="Rank to pair to role.", role="Role to pair to rank.")
    @app_commands.guilds(
        *[discord.Object(id=guild_id) for guild_id in Config.test_guild]
    )
    async def configure(
        self, interaction: discord.Interaction, rank: Rank, role: discord.Role
    ):
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

    def cog_unload(self):
        # self.cull.cancel()
        pass
