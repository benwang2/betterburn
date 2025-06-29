from typing import Union

from ...constants import GuildRoles, Rank
from ...signals import onUserLinked, onUserUnlinked
from ..database import SQLAlchemySession
from .models import MembershipTable, RoleTable, UserTable


def get_roles_for_guild(guild_id) -> GuildRoles:
    db = SQLAlchemySession()

    roles = db.query(RoleTable).filter_by(guild_id=guild_id).all()

    if roles:
        guild_roles: GuildRoles = {}
        for role in roles:
            guild_roles[Rank(role.rank).name] = role.role_id
        return guild_roles

    return None


def get_role_id_for_rank(guild_id: int, rank: Rank) -> Union[int, None]:
    db = SQLAlchemySession()

    role = db.query(RoleTable).filter_by(guild_id=guild_id, rank=rank.value).first()
    if role:
        return role.role_id
    return None


def set_role_id_for_rank(guild_id: int, role_id: int, rank: Rank) -> bool:
    db = SQLAlchemySession()

    role = db.query(RoleTable).filter_by(guild_id=guild_id, rank=rank.value).first()

    if role:
        if role.role_id == role_id:
            return False
        role.role_id = role_id
    else:
        role = RoleTable(guild_id=guild_id, role_id=role_id, rank=rank.value)
        db.add(role)

    db.commit()

    return True


def get_steam_id(user_id) -> Union[int, None]:
    db = SQLAlchemySession()

    user = db.query(UserTable).filter_by(user_id=user_id).first()
    if user:
        return user.steam_id
    return None


def get_guild_ids_for_user(user_id) -> Union[list[int], None]:
    db = SQLAlchemySession()

    memberships = db.query(MembershipTable).filter_by(user_id=user_id).all()
    return [membership.guild_id for membership in memberships]


def get_users_iter():
    db = SQLAlchemySession()
    return db.query(UserTable)


async def link_user(user_id, steam_id):
    db = SQLAlchemySession()

    user = db.query(UserTable).filter_by(user_id=user_id).first()
    if user:
        user.steam_id = steam_id
    else:
        user = UserTable(user_id=user_id, steam_id=steam_id)
        db.add(user)

    await onUserLinked.emit(user.user_id, user.steam_id)
    db.commit()
    return user


async def unlink_user(user_id):
    db = SQLAlchemySession()

    user = db.query(UserTable).filter_by(user_id=user_id).first()
    if user:
        await onUserUnlinked.emit(user.user_id, user.steam_id)
        db.delete(user)
        db.commit()
        return user

    return None


# Example usage
if __name__ == "__main__":
    guild_id = 297229405552377856
    role_dict = get_roles_for_guild(297229405552377856)
    print(role_dict)
    # user_id = 76561197995460378  # Replace with the actual user_id
    # steam_id = get_steam_id(user_id)
    # if steam_id:
    #     print(f"Steam ID for user {user_id} is {steam_id}")
    # else:
    #     print(f"No Steam ID found for user {user_id}")
