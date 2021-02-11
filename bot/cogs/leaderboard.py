import discord, requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from discord.ext import commands

baseUrl = "https://steamcommunity.com/stats/383980/leaderboards/"
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
    "etalus":"3277596"
}

font_colors = {
    "default":[(0, 0, 0, 0),(0,0,0),(255,255,255)],
    "bronze":[(0, 0, 0, 0),(0,0,0),(255,153,102)],
    "silver":[(0, 0, 0, 0),(0,0,0),(200,200,200)],
    "gold":[(0, 0, 0, 0),(0,0,0),(255,204,0)]
}

characters = ["zetterburn","orcane","forsburn","etalus","ori","clairen","elliana","wrastor","kragg","maypul","absa","ranno","sylvanos","shovel knight"]
aliases = [["zetterburn","zetter","zet"],["forsburn","fors"],["etalus","eta"],["elliana","elli"],["sylvanos","sylv"],["shovel knight","sk"]]

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

def generateCharacter(img, pos, char, scale=4, colors=font_colors["default"]):
    for x in range(0, len(cmatrix[char])):
        for y in range(0, len(cmatrix[char][0])):
            for dx in range(0, scale):
                for dy in range(0, scale):
                    if (cmatrix[char][x][y] == 0 and not img.getpixel(pos) != colors[0]) or cmatrix[char][x][y] > 0:
                        img.putpixel((pos[0]+x*scale+dx,pos[1]+y*scale+dy),colors[cmatrix[char][x][y]])
    return getTextWidth(char)

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

class cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def matchCharacter(self, character):
        for group in aliases:
            if character in group:
                return group[0]
        return False
    
    @commands.command()
    async def ranked(self, ctx, character):
        if self.matchCharacter(character) or (character in characters) or (character in leaderboards):
            character = character if (character in characters) or (character in leaderboards) else self.matchCharacter(character)
            await ctx.message.add_reaction("✅")
            try:
                with requests.get(baseUrl+leaderboards[character]) as response:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    entries = soup.findAll("div", {"class": "lbentry"})
                    names = soup.findAll("a", {"class":"playerName"})
                    scores = soup.findAll("div",{"class":"score"})
                    cell = 0
                    leaderboard = createLeaderboard()
                    for cell in range(0, len(entries)):
                        name = cleanText(names[cell].text)
                        score = eval(scores[cell].text.strip().replace(",",""))
                        if character in characters:
                            setPlayerMain(leaderboard, cell, character)
                        setPlayerName(leaderboard, cell, name)
                        setPlayerScore(leaderboard, cell, score)
                    with BytesIO() as binary:
                        leaderboard.save(binary, 'PNG')
                        binary.seek(0)
                        await ctx.send(file=discord.File(fp=binary, filename="leaderboard.png"))
            except Exception as e:
                print("Exception occured in !ranked command:",e)
                await ctx.message.clear_reactions()
                await ctx.message.add_reaction("💢")
        else:
            await ctx.message.add_reaction("😕")