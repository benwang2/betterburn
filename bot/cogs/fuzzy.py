import discord
from discord.ext import commands

su_ex = ["""```Shine can be jumpcancelled. During the startup of your jump, you can input an upsmash, which cancels your jump. Shine upstrong is most commonly used as a parry punish, in which case you would shine upstrong out of initial dash.```""",
"""```1. Neutral Special\n2. Jump\n3. Upsmash```"""]

pf_ex = ["""```Down Special can be cancelled with an airdodge. During the startup of Down B, you can input an airdodge, which cancels the dive with a flip. If you flip towards the stage, do a quarter circle back, you will flip towards the stage and then when you land, you'll roll back off the platform quickly.```""",
"""```1. Down Special\n2. Air Dodge\n3. Quarter Circle Back```"""]

ld_ex = ["""```Air dodge can be used immediately after a wall tech. Aim your recovery for the corner of the ledge and airdodge to the right/left just after a wall tech. Timings will vary depending on distance and tighter ledgedashes will give you more i-frames.```""",
"""```1. Wall tech\n2. Air Dodge Left/Right```"""]

resources = [
    [[ ["!shine", 2, 1, 2, 0, 2, [2,4]] ],"https://gfycat.com/higharidhammerheadshark  *(right trigger bound to strong)*", su_ex],
    [[ ["!shine", 2, 1, 2, 0, 2, 3] ],"https://gfycat.com/severalheartfelthairstreak  *(z bound to strong)*", su_ex],
    [[ ["!pity", 2, "flip", 2, [2,4]]],"https://gfycat.com/whisperedeagerbuck\n", pf_ex],
    [[ ["!pity", 2, "flip", 2, 3]],"https://gfycat.com/grayhighlevelarrowworm\n", pf_ex],
    [["!ledgedash"],"https://gfycat.com/officialfalsecrocodileskink\n", ld_ex],
    [["!shine","!shine angles"],"https://i.imgur.com/Zf6Ywes.png"],
    [["!backshot"],"https://gfycat.com/IndolentShortIndigowingedparrot"],
    [["!shmoost"],"https://gfycat.com/unknownforsakenaztecant-rivalsofaether"],
    [["!betterburn"],"```\nCommands\n1. !shine upstrong\n2. !shine upstrong [xbone/gcc]\n3. !pity flip\n4. !pity flip [xbone/gcc]\n5. !ledgedash\n6. !sdi \n7. !shine angles\n8. !ranked [character] [page]\n9. !text [content]\n10. !invite```"],
    [["!thegizmo"],"https://gfycat.com/hardfrightenedaustralianfurseal"],
    [["!thejarek"],"https://gfycat.com/uniformornerychrysomelid"],
    [["!the10s"],"https://gfycat.com/failingunrealisticcougar"],
    [["!sdi"],"https://gfycat.com/insecurepolishedarmyant"],
    [["!invite"],"https://discord.com/oauth2/authorize?client_id=704757052991602688&permissions=116800&scope=bot"]
]

my_icon = "https://cdn.discordapp.com/app-icons/704757052991602688/4950ad6ade639ed08a8c4b56ca5a6134.png"

matches = [  # order longest to shortest
    ["strong","smash"],
    ["up","u"],
    [" ","-",""],
    ["gamecube","gcc","gc"],
    ["xbone","xbox","xb"],
]

def match_group(message, group):
    for match in group:
        if match == message[:len(match)]:
            return match
    return None

def fuzzy(message, resource):
    for match in resource[0][0]:
        if isinstance(match,str) and match == message[:len(match)]:
            message = message[len(match):]
        elif isinstance(match,int) and match_group(message, matches[match]) != None:
            message = message[len(match_group(message, matches[match])):]
        elif isinstance(match,list):
            for group in match:
                if match_group(message, matches[group]) != None:
                    message = message[len(match_group(message, matches[group])):]

    return resource if message.strip() == "" else None
        
def match(message):
    for resource in resources:
        if isinstance(resource[0][0], list):
            result = fuzzy(message, resource)
            if result != None: return result 
        elif message in resource[0]:
            return resource
    
    return None


class cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if (message.author.bot): return
        if (message.content[0] != "!"): return

        item = match(message.content.lower())

        if item != None: 
            await message.channel.send(item[1])

            if len(item)==3:
                embed = discord.Embed(color=discord.Color.from_rgb(255,125,0))
                embed.add_field(name="Explanation",value=item[2][0], inline=False)
                embed.add_field(name="Inputs",value=item[2][1], inline=False)
                embed.set_footer(text="Betterburn",icon_url=my_icon)
                await message.channel.send(embed=embed)