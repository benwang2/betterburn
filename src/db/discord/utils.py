from .models import UserTable, RoleTable
from ..database import SQLAlchemySession
from signals import onUserLinked, onUserUnlinked


def get_steam_id(user_id):
    db = SQLAlchemySession()

    user = db.query(UserTable).filter_by(user_id=user_id).first()
    if user:
        return user.steam_id
    return None


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
    user_id = 76561197995460378  # Replace with the actual user_id
    steam_id = get_steam_id(user_id)
    if steam_id:
        print(f"Steam ID for user {user_id} is {steam_id}")
    else:
        print(f"No Steam ID found for user {user_id}")
