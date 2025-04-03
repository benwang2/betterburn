from enum import Enum
from typing import TypedDict
import discord


class Rank(Enum):
    Stone = 0
    Bronze = 1
    Silver = 2
    Gold = 3
    Platinum = 4
    Diamond = 5
    Master = 6
    Grandmaster = 7
    Aetherean = 8


class RankColors(Enum):
    Stone = discord.Color.dark_gray()
    Bronze = discord.Color.dark_orange()
    Silver = discord.Color.light_gray()
    Gold = discord.Color.gold()
    Platinum = discord.Color.lighter_gray()
    Diamond = discord.Color.blue()
    Master = discord.Color.brand_green()
    Grandmaster = discord.Color.red()
    Aetherean = discord.Color.purple()


class RoleDoctorOption(Enum):
    check = 0
    test = 1


class GuildRoles(TypedDict):
    Stone: int
    Bronze: int
    Silver: int
    Gold: int
    Platinum: int
    Diamond: int
    Master: int
    Grandmaster: int
    Aetherean: int
