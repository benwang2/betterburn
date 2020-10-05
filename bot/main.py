import os
import discord, asyncio

client = discord.Client()

__TOKEN = os.getenv("DISCORD_TOKEN")

resources = [
    [["!shine upstrong", "!shine ustrong", "!shine upsmash", "!shine usmash"],"https://gfycat.com/kaleidoscopicbeneficialflicker"],
    [["!shine upstrong gc","!shine ustrong gc","!shine upstrong gcc","!shine ustrong gcc"],"https://gfycat.com/meatydimpledamericancicada + *(z bound to strong)*"],
    [["!pityflip","!pity flip"],"https://gfycat.com/whisperedeagerbuck"],
    [["!pityflip gcc","!pity flip gcc"],"https://gfycat.com/grayhighlevelarrowworm"],
    [["!shine","!shine angles"],"https://i.imgur.com/Zf6Ywes.png"],
    [["!backshot"],"https://gfycat.com/IndolentShortIndigowingedparrot"],
    [["!shmoost"],"https://gfycat.com/unknownforsakenaztecant-rivalsofaether"],
    [["!betterburn"],"```\nCommands\n1. !shine upstrong\n2. !shine upstrong gcc\n3. !pity flip\n4. !pity flip gcc\n5. !shine angles```"]
]

@client.event
async def on_message(message):
    if (message.author==client.user or message.author.bot):
        return
    for r in resources:
        if message.content.lower() in r[0]:
            await message.channel.send(r[1])
            return

client.run(__TOKEN)
