from typing import Any, Union

import discord

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


async def sync_user_memberships(user_id: int, bot: Any) -> dict[str, list[int]]:
    db = SQLAlchemySession()

    removed_guild_ids: list[int] = []
    created_guild_ids: list[int] = []
    synced_guild_ids: list[int] = []

    try:
        memberships = db.query(MembershipTable).filter_by(user_id=user_id).all()
        membership_guild_ids = {membership.guild_id for membership in memberships}

        for membership in memberships:
            guild = bot.get_guild(membership.guild_id)
            if guild is None:
                removed_guild_ids.append(membership.guild_id)
                db.delete(membership)
                continue

            member = guild.get_member(user_id)
            if member is None:
                try:
                    member = await guild.fetch_member(user_id)
                except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                    member = None

            if member is not None:
                synced_guild_ids.append(guild.id)

        for guild in bot.guilds:
            if guild.id in membership_guild_ids:
                continue

            member = guild.get_member(user_id)
            if member is None:
                try:
                    member = await guild.fetch_member(user_id)
                except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                    member = None

            if member is None:
                continue

            db.add(MembershipTable(user_id=user_id, guild_id=guild.id))
            created_guild_ids.append(guild.id)
            synced_guild_ids.append(guild.id)

        db.commit()

        return {
            "removed_guild_ids": removed_guild_ids,
            "created_guild_ids": created_guild_ids,
            "synced_guild_ids": synced_guild_ids,
        }
    finally:
        close = getattr(db, "close", None)
        if callable(close):
            close()


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
