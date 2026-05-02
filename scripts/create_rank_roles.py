import argparse
import asyncio

import discord

from src.config import Config
from src.constants import Colors, Rank
from src.custom_logger import CustomLogger as Logger

logger = Logger("discord_role_seed")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
target_guild_id: int | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create Betterburn rank roles in a Discord guild.")
    parser.add_argument("guild_id", type=int, help="The Discord guild ID to seed with rank roles.")
    return parser.parse_args()


async def ensure_rank_roles(guild_id: int) -> None:
    await client.wait_until_ready()

    guild = client.get_guild(guild_id)
    if guild is None:
        guild = await client.fetch_guild(guild_id)

    logger.info(f"Seeding rank roles for guild <name={guild.name} id={guild.id}>")

    for rank in Rank:
        role_name = rank.name
        role_color = discord.Color(Colors[rank.name].value)
        existing_role = discord.utils.get(guild.roles, name=role_name)

        if existing_role is None:
            # await guild.create_role(
            #     name=role_name,
            #     color=role_color,
            #     reason="Seed Betterburn rank roles",
            # )
            logger.info(f"Create role '{role_name}' in guild <name={guild.name} id={guild.id}>")
            continue

        if existing_role.color != role_color:
            # await existing_role.edit(
            #     name=role_name,
            #     color=role_color,
            #     reason="Normalize Betterburn rank role",
            # )
            logger.info(f"Update role '{role_name}' in guild <name={guild.name} id={guild.id}>")
            continue

        logger.info(f"Role '{role_name}' already exists in guild <name={guild.name} id={guild.id}>")

    logger.info(f"Finished seeding rank roles for guild <name={guild.name} id={guild.id}>")


@client.event
async def on_ready() -> None:
    global target_guild_id

    if target_guild_id is None:
        logger.error("No target guild configured for rank role seeding")
        return

    try:
        await ensure_rank_roles(target_guild_id)
    except Exception:
        logger.error(f"Failed to seed rank roles for guild_id={target_guild_id}", exc_info=True)
        raise
    finally:
        if not client.is_closed():
            await client.close()


async def run_once(guild_id: int) -> None:
    global target_guild_id

    target_guild_id = guild_id


async def main() -> None:
    args = parse_args()
    await run_once(args.guild_id)
    await client.start(Config.discord_token)


if __name__ == "__main__":
    asyncio.run(main())
