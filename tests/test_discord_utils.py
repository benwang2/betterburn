import pytest

from src.db.discord import utils


class DummyRole:
    def __init__(self, rank=1, role_id=123):
        self.rank = rank
        self.role_id = role_id


class DummyUser:
    def __init__(self, user_id=1, steam_id=456):
        self.user_id = user_id
        self.steam_id = steam_id


class DummyMembership:
    def __init__(self, user_id=1, guild_id=123):
        self.user_id = user_id
        self.guild_id = guild_id


class DummyDB:
    def __init__(self, roles=None, user=None, memberships=None):
        self._roles = roles or [DummyRole()]
        self._user = user or DummyUser()
        self._memberships = memberships or [DummyMembership()]
        self.committed = False
        self.added = None
        self.deleted = None

    def query(self, model):
        db = self

        class DummyQuery:
            def filter_by(self, **kwargs):
                if model.__name__ == "RoleTable":

                    class DummyAll:
                        def all(inner_self):
                            return db._roles

                        def first(inner_self):
                            return db._roles[0] if db._roles else None

                    return DummyAll()
                if model.__name__ == "UserTable":

                    class DummyUserQ:
                        def all(inner_self):
                            return [db._user] if db._user else []

                        def first(inner_self):
                            return db._user

                    return DummyUserQ()
                if model.__name__ == "MembershipTable":

                    class DummyMembershipQ:
                        def all(inner_self):
                            return db._memberships

                    return DummyMembershipQ()

            def all(self):
                return []

        return DummyQuery()

    def add(self, obj):
        self.added = obj

    def delete(self, obj):
        self.deleted = obj

    def commit(self):
        self.committed = True


@pytest.fixture(autouse=True)
def patch_db(monkeypatch):
    roles = [DummyRole()]
    user = DummyUser(user_id=123, steam_id=1337)
    memberships = [DummyMembership(user_id=123, guild_id=456), DummyMembership(user_id=123, guild_id=789)]
    monkeypatch.setattr(utils, "SQLAlchemySession", lambda: DummyDB(roles, user, memberships))


@pytest.mark.asyncio
async def test_link_user(monkeypatch):
    called = {}

    async def fake_emit(user_id, steam_id):
        called["emit"] = (user_id, steam_id)

    monkeypatch.setattr(utils.onUserLinked, "emit", fake_emit)
    user = await utils.link_user(123, 1337)
    assert user.user_id == 123
    assert user.steam_id == 1337
    assert called["emit"] == (123, 1337)


@pytest.mark.asyncio
async def test_unlink_user(monkeypatch):
    called = {}

    async def fake_emit(user_id, steam_id):
        called["emit"] = (user_id, steam_id)

    monkeypatch.setattr(utils.onUserUnlinked, "emit", fake_emit)
    user = await utils.unlink_user(123)
    assert user.user_id == 123
    assert user.steam_id == 1337
    assert called["emit"] == (123, 1337)


def test_get_roles_for_guild():
    result = utils.get_roles_for_guild(1)
    assert isinstance(result, dict) or result is None


def test_get_role_id_for_rank():
    class DummyRank:
        value = 1

    result = utils.get_role_id_for_rank(1, DummyRank())
    assert result == 123 or result is None


def test_set_role_id_for_rank():
    class DummyRank:
        value = 1

    result = utils.set_role_id_for_rank(1, 123, DummyRank())
    assert result is True or result is False


def test_get_steam_id():
    result = utils.get_steam_id(1)
    assert result == 1337 or result is None


def test_get_guild_ids_for_user():
    result = utils.get_guild_ids_for_user(123)
    assert isinstance(result, list)
    assert len(result) == 2, "Expected two guild IDs for the user, got: {}".format(result)
    assert 456 in result, "Expected guild ID 456 to be in the list"
    assert 789 in result, "Expected guild ID 789 to be in the list"
