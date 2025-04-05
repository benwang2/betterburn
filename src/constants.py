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
