import os, time, random
import discord, asyncio
from cogs import presence

client = discord.ext.commands.Bot('!')

__TOKEN = os.getenv("DISCORD_TOKEN")

su_ex = """```
Explanation: Shine can be jumpcancelled. During the startup of your jump, you can input an
upsmash, which cancels your jump. So if you have momentum out of the shine, you can carry
that into your upsmash.

Inputs:
1. Neutral Special
2. Jump
3. Upsmash
``` 
"""

pf_ex = """```
Explanation: Down Special can be cancelled with an airdodge. During the startup up Down B,
you can input an airdodge, which cancels the dive with a flip. If you flip towards the stage,
do a quarter circle back, you will flip towards the stage and then when you land, you'll roll
back off the platform quickly.

Inputs:
1. Down Special
2. Air Dodge
3. Quarter Circle Back
```"""

resources = [
    [["!shine upstrong", "!shine ustrong", "!shine upsmash", "!shine usmash"],"https://gfycat.com/kaleidoscopicbeneficialflicker  *(right trigger bound to strong)*\n"+su_ex],
    [["!shine upstrong gc","!shine ustrong gc","!shine upstrong gcc","!shine ustrong gcc"],"https://gfycat.com/meatydimpledamericancicada  *(z bound to strong)*\n"+su_ex],
    [["!pityflip","!pity flip"],"https://gfycat.com/whisperedeagerbuck\n"+pf_ex],
    [["!pityflip gcc","!pity flip gcc"],"https://gfycat.com/grayhighlevelarrowworm\n"+pf_ex],
    [["!shine","!shine angles"],"https://i.imgur.com/Zf6Ywes.png"],
    [["!backshot"],"https://gfycat.com/IndolentShortIndigowingedparrot"],
    [["!shmoost"],"https://gfycat.com/unknownforsakenaztecant-rivalsofaether"],
    [["!betterburn"],"```\nCommands\n1. !shine upstrong\n2. !shine upstrong gcc\n3. !pity flip\n4. !pity flip gcc\n5. !shine angles```"]
]

f_resources = [ # for fuzzy matching
    ["!shine",2,1,2,0,2,[3,4,2]], # shine upstrong
    ["!pity",2,"flip",2,[3,4,2]], # pity flip
]
matches = [  # order longest to shortest
    ["strong","smash"],
    ["up","u"],
    [" ","-",""],
    ["gamecube","gcc","gc"],
    ["xbone","xbox","xb"],
]

def match(msg,i=0,k=None,group=-1):
    if i == 0:
        for j in range(0, len(f_resources)):
            r = f_resources[j]
            if msg[0:len(r[i])] == r[i]:
                return match(msg[len(r[i]):],i+1,j)
    elif i > 0 and i < len(f_resources[k]):
        if isinstance(f_resources[k][i],int):
            for variant in matches[f_resources[k][i]]:
                if msg[0:len(variant)] == variant:
                    return match(msg[len(variant):],i+1,k,f_resources[k][i])
        elif isinstance(f_resources[k][i],list):
            for variants in f_resources[k][i]:
                for variant in matches[variants]:
                    if msg[0:len(variant)] == variant:
                        return match(msg[len(variant):],i+1,k,variants)
        elif isinstance(f_resources[k][i],str):
            if f_resources[k][i]==msg[0:len(f_resources[k][i])]:
                return match(msg[len(f_resources[k][i]):],i+1,k)
    if len(msg) == 0:
        return k, group
    return -1

@client.event
async def on_message(message):

    if (message.author==client.user or message.author.bot):
        return

    for r in resources:
        if message.content.lower() in r[0]:
            await message.channel.send(r[1])
            return

    idx, group = match(message.content.lower())
    if idx > -1:
        if idx == 0:
            if group == 2 or group == 4:
                await message.channel.send(resources[0][1])
            if group == 3:
                await message.channel.send(resources[1][1])
        elif idx == 1:
            if group == 2 or group == 4:
                await message.channel.send(resources[2][1])
            if group == 3:
                await message.channel.send(resources[3][1])
        return

@client.event
async def on_ready():
    print("betterburn online, v1.05")
    client.add_cog(presence.cog(client))    


client.run(__TOKEN)
