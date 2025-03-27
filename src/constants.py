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


class GuildRoles(TypedDict):
    Stone: int
    Bronze: int
    Silver: int
    Gold: int
    Platinum: int
    Diamond: int
    Master: int
