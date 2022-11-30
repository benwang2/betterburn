from typing import List

import disnake, requests, os
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from disnake.ext import commands
from modules.steamboards import SteamLeaderboard

baseUrl = f"https://steamcommunity.com/stats/{os.environ['STEAM_APP_ID']}/leaderboards/"
my_icon = "https://cdn.discordapp.com/app-icons/704757052991602688/4950ad6ade639ed08a8c4b56ca5a6134.png"
leaderboards = {
    "all":"3277611",
    "random":"3279662",
    "ori":"3277598",
    "ranno":"3277599",
    "clairen":"3277600",
    "sylvanos":"3277601",
    "elliana":"3277602",
    "shovel knight":"3277603",
    "zetterburn":"3277587",
    "orcane":"3277588",
    "wrastor":"3277590",
    "kragg":"3277591",
    "forsburn":"3277592",
    "maypul":"3277593",
    "absa":"3277595",
    "etalus":"3277596",
    "olympia":"6690115",
    "mollo":"6690110",
    "hodan":"6690112",
    "pomme":"6690113"
}

font_colors = { # transparent,  outline,    fill color
    "default":  [(0, 0, 0, 0),  (0, 0, 0),  (255, 255, 255)],
    "bronze":   [(0, 0, 0, 0),  (0, 0, 0),  (255, 153, 102)],
    "silver":   [(0, 0, 0, 0),  (0, 0, 0),  (200, 200, 200)],
    "gold":     [(0, 0, 0, 0),  (0, 0, 0),  (255, 204, 0  )]
}

characters = [
    "zetterburn","orcane","forsburn","etalus",
    "ori","clairen","elliana","wrastor",
    "kragg","maypul","absa","ranno",
    "sylvanos","shovel knight",
    "olympia","mollo","hodan","pomme"
]
aliases = [
    ["zetterburn","zetter","zet"],
    ["forsburn","fors"],
    ["etalus","eta"],
    ["elliana","elli"],
    ["sylvanos","sylv"],
    ["shovel knight","sk"],
    ["olympia","oly"]
]

cmatrix = {}
with open("bot/assets/leaderboard/cmatrix.csv","r",encoding="utf8") as f:
    for data in f.readlines():
        data = data.replace("\n","")
        char = data[0]
        cmatrix[char] = []
        data = data[2:].split(",")
        width, height = data.pop(0), data.pop(0)
        for x in range(0, eval(width)):
            cmatrix[char].append([])
            for y in range(0, eval(height)):
                cmatrix[char][x].append(eval(data.pop(0)))

def cleanText(text):
    text = text.upper()
    for char in text:
        if not char in cmatrix:
            text = text.replace(char,"")
    return text

def createLeaderboard():
    leaderboard = Image.open("bot/assets/leaderboard/leaderboard.png")
    return leaderboard

def getTextWidth(text, scale = 4):
    width = 0
    for char in text:
        width += len(cmatrix[char])*scale + (scale if char==" " else -scale)
    return width

def generateCharacter(img, pos, char, scale = 4, colors = font_colors["default"]):
    try:
        for x in range(0, len(cmatrix[char])):
            for y in range(0, len(cmatrix[char][0])):
                for dx in range(0, scale):
                    for dy in range(0, scale):
                        if (cmatrix[char][x][y] == 0 and not img.getpixel(pos) == colors[0]) or cmatrix[char][x][y] > 0:
                            img.putpixel((pos[0]+x*scale+dx,pos[1]+y*scale+dy),colors[cmatrix[char][x][y]])
    except Exception as e:
        raise e
    return getTextWidth(char, scale)

def setPlayerName(img, cell, name):
    name = cleanText(name)
    offset = 0
    for char in name:
        offset += generateCharacter(img, (152+offset, 56+48*cell), char)

def setPlayerMain(img, cell, name):
    if name.lower() in characters:
        with Image.open("bot/assets/leaderboard/charicons.png") as assets:
            offset = characters.index(name.lower())*36
            char = assets.crop((0, offset, 92, offset + 36))
            img.paste(char, (644, 60+(48*cell), 644+92, 96+(48*cell)), char)

def setPlayerScore(img, cell, points):
    colors = font_colors["default"]
    if points > 1200: colors = font_colors["bronze"]
    if points > 1500: colors = font_colors["silver"]
    if points > 1800: colors = font_colors["gold"]
    offset = 0
    for char in "🏆 "+str(points):
        offset += generateCharacter(img, (806+offset, 56+48*cell), char , colors=colors)

def setPlayerRank(img, cell, rank):
    width = getTextWidth(rank)
    offset = 0
    for char in rank:
        offset += generateCharacter(img, (66-int(width/2)+4+offset, 56+48*cell), char)

class Leaderboard(commands.Cog):
    # async def autocomplete_char(inter, string: str) -> List[str]:
    #     return [name for name in leaderboards.keys() if string.lower() in name.lower()]

    @commands.slash_command(
        name="ranked",
        description="Display the leaderboard for a character category."
    )
    async def ranked(
        inter: disnake.CommandInteraction,
        character: str = commands.Param(choices=leaderboards.keys()),
        page: int = 1
    ):
        if not character in leaderboards:
            await inter.response.send_message("Please enter a valid character.", ephemeral=True)
            return

        steamboard = SteamLeaderboard(
            app_id = os.environ["STEAM_APP_ID"],
            leaderboard_id = leaderboards[character],
            api_key = os.environ["STEAM_API_KEY"],
            mute=True
        )

        page_start = 1+((page-1)*15)

        try:
            (data, real_page) = steamboard.update(start=page_start, limit=16).values()
        except Exception as e:
            embed = disnake.Embed(
                title="An unknown error has occurred!",
                description="Please contact <@154046172254830592>.",
                color=disnake.Color.from_rgb(255,125,0)
            )
            embed.add_field(name="Error",value=repr(e), inline=False)
            await inter.response.send_message(embed=embed, ephemeral=True)
            return

        users = data.values()

        cell = 0
        try:
            leaderboard = createLeaderboard()
            
            for i in range(0, min(15, len(users))):
                name = cleanText(users[i]["persona"])
                score = eval(users[i]["score"])
                rank = users[i]['rank']
                if character in characters:
                    setPlayerMain(leaderboard, cell, character)
                setPlayerName(leaderboard, cell, name)
                setPlayerScore(leaderboard, cell, score)
                setPlayerRank(leaderboard, cell, str(rank))
                cell += 1
            
            file = None
            with BytesIO() as binary:
                leaderboard.save(binary, 'PNG')
                binary.seek(0)
                file = disnake.File(fp=binary, filename=f"betterburn_{character}{page}.png")

            embed = disnake.Embed(
                title=f"Ranked - {character.capitalize()}",
                description = f"Page {real_page}",
                color=disnake.Color.from_rgb(255,125,0)
            )
            embed.set_image(url=f"attachment://betterburn_{character}{page}.png")
            embed.set_footer(text="Betterburn",icon_url=my_icon)

            await inter.response.send_message(embed=embed, file=file)
        except Exception as e:
            embed = disnake.Embed(
                title="An unknown error has occurred!",
                description="Please contact <@154046172254830592>.",
                color=disnake.Color.from_rgb(255,125,0)
            )
            embed.add_field(name="Error",value=repr(e), inline=False)
            embed.set_footer(text="Betterburn",icon_url=my_icon)
            
            await inter.response.send_message(embed=embed, ephemeral=True)


    @commands.slash_command(name="text", description="Generates text in Rivals of Aether font.")
    async def text(inter, text: str):
        try:
            tooLong = len(text) > 1024
            if tooLong: text = text[:1024]+"..."

            text = cleanText(text.lower())

            offset = [0,0]
            textSize = 4
            maxRowWidth = 250*textSize
            rowHeight = textSize*10
            rows, rowWidth = [[]], 0
            
            for word in text.split(" "):
                if getTextWidth(word, scale=textSize) > maxRowWidth: # break word into two rows
                    segEnd = 0
                    while segEnd != len(word):
                        segEnd += 1
                        if getTextWidth(word[:segEnd],scale=textSize) > maxRowWidth:
                            rows[-1].append(word[:segEnd-1])
                            word = word[segEnd-1:]
                            segEnd = 0
                            rows.append([])
                            rowWidth = 0
                        elif segEnd == len(word):
                            rows[-1].append(word)
                            rowWidth = getTextWidth(word+" ",scale=textSize)
                else:
                    if (rowWidth + getTextWidth(word,scale=textSize) >= maxRowWidth):
                        rows.append([])
                        rowWidth = 0
                    rows[-1].append(word)
                    rowWidth += getTextWidth(word+" ",scale=textSize)
    

            imageBounds = (min(getTextWidth(text,scale=textSize)+4,maxRowWidth)+12*textSize,len(rows)*rowHeight)
            img = Image.new("RGBA",imageBounds)
            offset = [0, 0]
            for rowNum in range(len(rows)):
                for word in rows[rowNum]:
                    for char in word:
                        offset[0] += generateCharacter(img, (offset[0], -4+(rowHeight*rowNum)), char, scale=textSize)
                    offset[0] += generateCharacter(img, (offset[0], -4+(rowHeight*rowNum)), " ", scale=textSize)
                offset[0] = 0
                        
            with BytesIO() as binary:
                img.save(binary, "PNG")
                binary.seek(0)
                if tooLong:
                    embed = disnake.Embed(
                        title="An error has occurred!",
                        color=disnake.Color.from_rgb(255,125,0)
                    )
                    embed.add_field(name="Error",value="Your message was too long to generate completely. (limit 1024 characters)", inline=False)
                    embed.set_footer(text="Betterburn",icon_url=my_icon)
                    await inter.response.send_message(
                        embed=embed,
                        ephemeral=True
                    )
                else:
                    file = disnake.File(fp=binary, filename=f"betterburn_text.png")
                    embed = disnake.Embed(
                        color=disnake.Color.from_rgb(255,125,0)
                    )
                    embed.set_image(url=f"attachment://betterburn_text.png")
                    embed.set_footer(text="Betterburn",icon_url=my_icon)

                    await inter.response.send_message(
                        embed=embed,
                        file=file
                    )
        except Exception as e:
            embed = disnake.Embed(
                title="An unknown error has occurred!",
                description="Please contact <@154046172254830592>.",
                color=disnake.Color.from_rgb(255,125,0)
            )
            embed.add_field(name="Error",value=repr(e), inline=False)
            embed.set_footer(text="Betterburn",icon_url=my_icon)
            
            await inter.response.send_message(embed=embed, ephemeral=True)