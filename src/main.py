from db.database import init_db


def test_cache():
    from time import perf_counter_ns
    from db.cache.utils import (
        # insert_example_data,
        # query_example_data,
        get_score_by_steam_id,
        bulk_insert_cache_from_file,
        clear_cache_table,
    )

    # with open("./data.csv","r")
    t_start = perf_counter_ns()
    clear_cache_table()
    print(f"Took {(perf_counter_ns()-t_start)/1_000_000_000}s to clear cache table.")
    t_start = perf_counter_ns()
    bulk_insert_cache_from_file("./data.csv")
    print(f"Took {(perf_counter_ns()-t_start)/1_000_000_000}s to refresh cache table.")
    # query_example_data()


def test_query_cache():
    from db.discord.utils import get_steam_id

    user_id = 76561197995460378  # Replace with the actual user_id
    steam_id = get_steam_id(user_id)

    print(steam_id)


def test_steamboard():
    from steamboard.steamboard import SteamLeaderboard

    app_id = 2217000
    leaderboard_id = 14800950

    board = SteamLeaderboard(
        app_id=app_id, leaderboard_id=leaderboard_id, api_key=None, mute=False
    )
    board.update()

    print(
        f"There are {len(board)} rows in <Steamboard app={app_id} leaderboard={leaderboard_id}>"
    )


def test_auth():
    from db.auth.utils import create_or_extend_session

    sess = create_or_extend_session(discord_id=0)
    print(sess)


def test_api():
    from api import api


if __name__ == "__main__":
    import db.auth.utils

    init_db()
    test_api()
    # test_auth()

    # board = SteamLeaderboard(2217000, 14800950, False)
    # board.update()

    # test_cache()
    # test_query_cache()
    # test_steamboard()
