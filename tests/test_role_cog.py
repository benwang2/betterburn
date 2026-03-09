from types import SimpleNamespace

import pytest

from src.bot.cogs.roles import RoleAssignmentResult, RoleCog
from src.constants import Rank
from src.leaderboard_api import LeaderboardStanding


class DummyRole:
    def __init__(self, role_id, name):
        self.id = role_id
        self.name = name


class DummyGuild:
    def __init__(self, guild_id, roles):
        self.id = guild_id
        self.roles = roles


class DummyMember:
    def __init__(self, member_id, guild, roles):
        self.id = member_id
        self.guild = guild
        self.roles = roles
        self.name = "Ben"
        self.added_roles = []
        self.removed_roles = []

    async def add_roles(self, *roles):
        self.added_roles.extend(roles)

    async def remove_roles(self, *roles):
        self.removed_roles.extend(roles)


class FakeLeaderboardApi:
    def __init__(self, standing):
        self.standing = standing

    async def get_standing_async(self, steam_id):
        assert steam_id == 76561198000000000
        return self.standing


@pytest.mark.asyncio
async def test_assign_roles_uses_leaderboard_api(monkeypatch):
    import src.bot.cogs.roles as roles_module

    standing = LeaderboardStanding(
        steam_id="76561198000000000",
        playfab_id="PLAYFAB123",
        stat_value=950,
        position=50,
        timestamp="2026-03-09T12:34:56+00:00",
    )

    monkeypatch.setattr(roles_module, "get_steam_id", lambda user_id: 76561198000000000)
    monkeypatch.setattr(roles_module, "get_role_id_for_rank", lambda guild_id, rank: 30)
    monkeypatch.setattr(
        roles_module,
        "get_roles_for_guild",
        lambda guild_id: {
            Rank.Bronze.name: 10,
            Rank.Silver.name: 20,
            Rank.Gold.name: 30,
        },
    )

    guild_roles = [DummyRole(10, Rank.Bronze.name), DummyRole(20, Rank.Silver.name), DummyRole(30, Rank.Gold.name)]
    member = DummyMember(123, DummyGuild(456, guild_roles), [DummyRole(10, Rank.Bronze.name)])

    cog = RoleCog(bot=SimpleNamespace())
    cog.leaderboard_api = FakeLeaderboardApi(standing)

    success, result = await cog.assign_roles(member)

    assert success is True
    assert isinstance(result, RoleAssignmentResult)
    assert result.rank == Rank.Gold
    assert [role.id for role in member.added_roles] == [30]
    assert [role.id for role in member.removed_roles] == [10, 20]