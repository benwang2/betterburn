from typing import List

import disnake
from disnake.ext import commands

my_icon = "https://cdn.discordapp.com/app-icons/704757052991602688/4950ad6ade639ed08a8c4b56ca5a6134.png"
tech_list = ["shine upstrong","pityflip","ledgedash","sdi"]
controller_list = ["xbox one","gamecube"]
resources = {
    "shine upstrong": {
        "xbox one": "https://gfycat.com/higharidhammerheadshark",#  *(right trigger bound to strong)*",
        "gamecube": "https://gfycat.com/severalheartfelthairstreak",#  *(z bound to strong)",
        "__embed__": ["""```Shine can be jumpcancelled. During the startup of your jump, you can input an upsmash, which cancels your jump. Shine upstrong is most commonly used as a parry punish, in which case you would shine upstrong out of initial dash.```""", """```1. Neutral Special\n2. Jump\n3. Upsmash```"""]
    },
    "pityflip": {
        "xbox one": "https://gfycat.com/whisperedeagerbuck",
        "gamecube": "https://gfycat.com/grayhighlevelarrowworm",
        "__embed__": ["""```Down Special can be cancelled with an airdodge. During the startup of Down B, you can input an airdodge, which cancels the dive with a flip. If you flip towards the stage, do a quarter circle back, you will flip towards the stage and then when you land, you'll roll back off the platform quickly.```""", """```1. Down Special\n2. Air Dodge\n3. Quarter Circle Back```"""]
    },
    "ledgedash": {
        "xbox one": "https://gfycat.com/officialfalsecrocodileskink",
        "gamecube": "https://gfycat.com/officialfalsecrocodileskink",
        "__embed__": ["""```Air dodge can be used immediately after a wall tech. Aim your recovery for the corner of the ledge and airdodge to the right/left just after a wall tech. Timings will vary depending on distance and tighter ledgedashes will give you more i-frames.```""", """```1. Wall tech\n2. Air Dodge Left/Right```"""]
    },
    "sdi": {
        "xbox one": "",
        "gamecube": "",
    }
}

class Guide(commands.Cog):

    async def autocomplete_name(inter, string: str) -> List[str]:
        return [name for name in tech_list if string.lower() in name.lower()]

    async def autocomplete_controller(inter, string: str) -> List[str]:
        return [controller for controller in controller_list if string.lower() in controller.lower()]

    @commands.slash_command(
        name="guide",
        description="Access a tutorial on how to perform a certain tech."
    )
    async def guide(
        inter: disnake.CommandInteraction,
        name: str = commands.Param(choices=tech_list),
        controller: str = commands.Param(choices=controller_list)
    ):
        if name in resources:
            resource = resources[name]
            embed = None
            
            await inter.response.send_message(content=resource[controller.lower()])

            if "__embed__" in resource:
                item = resource["__embed__"]
                embed = disnake.Embed(color=disnake.Color.from_rgb(255,125,0))
                embed.add_field(name="Explanation",value=item[0], inline=False)
                embed.add_field(name="Inputs",value=item[1], inline=False)
                embed.set_footer(text="Betterburn",icon_url=my_icon)

                await inter.channel.send(embed=embed)
                
            
                