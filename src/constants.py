from enum import Enum
from typing import TypedDict


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


class Colors(Enum):
    Stone = 0x000000
    Bronze = 0x815502
    Silver = 0xB4B4C3
    Gold = 0xF1C40F
    Platinum = 0xA9C3DA
    Diamond = 0x0DDABE
    Master = 0x2ECC71
    Grandmaster = 0xE81042
    Aetherean = 0xD508E2


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
