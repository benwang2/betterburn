import asyncio

from src.bot.bot import TOKEN, client
from src.db.discord.utils import get_users_iter


def generate_memberships_for_all_users():
    users = get_users_iter()
    print(users)
    for user in users.yield_per(10):
        # Example: create a membership for each user
        print(user)


async def on_ready_and_run():
    await client.wait_until_ready()
    print(f"Bot is ready to run scripts: {client.user}")
    generate_memberships_for_all_users()
    # Call your function here
    # ...
    await client.close()


@client.event
async def on_ready():
    await on_ready_and_run()


async def main():
    await client.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
