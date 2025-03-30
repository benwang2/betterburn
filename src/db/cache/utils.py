import csv
from datetime import datetime, timezone

from ..database import SQLAlchemySession
from .models import LeaderboardRow, Metadata
from constants import Rank


# Insert example data into the cache table
def _insert_example_data():
    db = SQLAlchemySession()
    try:
        cache_entries = [
            LeaderboardRow(steam_id=12345, score=100, rank=1),
            LeaderboardRow(steam_id=67890, score=200, rank=2),
        ]
        db.add_all(cache_entries)
        db.commit()
    finally:
        db.close()


# Query example data from the cache table
def _query_example_data():
    db = SQLAlchemySession()
    try:
        cache_data = db.query(LeaderboardRow).all()
        print("Cache Table:")
        for entry in cache_data[:10]:
            print(
                f"Steam ID: {entry.steam_id}, Score: {entry.score}, Rank: {entry.rank}"
            )
        print("...")
    finally:
        db.close()


def update_metadata(num_rows):
    db = SQLAlchemySession()

    try:
        timestamp = datetime.now(timezone.utc)

        db.query(Metadata).delete()
        metadata_entry = Metadata(updated=timestamp, player_count=num_rows)
        db.add(metadata_entry)
    finally:
        db.close()


# Get score by Steam ID
def get_score_by_steam_id(steam_id):
    db = SQLAlchemySession()
    try:
        record = db.query(LeaderboardRow).filter_by(steam_id=steam_id).first()
        return record.score if record else None
    finally:
        db.close()


def get_rank_from_score(score) -> Rank:
    rank: Rank = Rank.Stone
    if score:
        if score >= 500 and score < 700:
            rank = Rank.Bronze
        elif score >= 700 and score < 800:
            rank = Rank.Silver
        elif score >= 800 and score < 1100:
            rank = Rank.Gold
        elif score >= 1100 and score < 1300:
            rank = Rank.Platinum
        elif score >= 1300 and score < 1500:
            rank = Rank.Diamond
        elif score >= 1500:
            rank = Rank.Master

    return rank


def bulk_insert_cache_from_list(leaderboard: list):
    """
    Bulk inserts records into the 'cache' table from a list.

    The file should have headers describing the columns.
    The index of the row (0-based) will be used as the 'rank'.

    Args:
        leaderboard (List<Dict>)
    """
    db = SQLAlchemySession()
    # print("Hi", file_path)
    try:
        records = []

        for steam_id, data in leaderboard:
            steam_id = int(steam_id)
            score = int(data.get("score"))
            rank = int(data.get("rank"))
            # print(steam_id, score, rank)
            records.append(LeaderboardRow(steam_id=steam_id, score=score, rank=rank))

        # Bulk insert using SQLAlchemy

        # Update metadata table with current timestamp and player count

        db.bulk_save_objects(records)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error occurred during bulk insert: {e}")
    finally:
        db.close()


def bulk_insert_cache_from_file(file_path):
    """
    Bulk inserts records into the 'cache' table from a CSV file.

    The file should have headers describing the columns.
    The index of the row (0-based) will be used as the 'rank'.

    Args:
        file_path (str): Path to the input CSV file.
    """
    db = SQLAlchemySession()
    # print("Hi", file_path)
    try:
        records = []
        with open(file_path, "r") as file:
            # print(file.readline())
            reader = csv.DictReader(file)  # Automatically uses headers as keys
            for _, row in enumerate(reader, start=1):  # Start rank at 1
                # Parse and create a LeaderboardRow object
                steam_id = int(row.get("steam_id"))
                score = int(row.get("score"))
                rank = int(row.get("rank"))
                # print(steam_id, score, rank)
                records.append(
                    LeaderboardRow(steam_id=steam_id, score=score, rank=rank)
                )

        # Bulk insert using SQLAlchemy

        # Update metadata table with current timestamp and player count

        db.bulk_save_objects(records)
        db.commit()
        print(f"Successfully inserted {len(records)} records into the 'cache' table.")
    except Exception as e:
        db.rollback()
        print(f"Error occurred during bulk insert: {e}")
    finally:
        db.close()


def clear_cache_table():
    db = SQLAlchemySession()
    try:
        db.query(LeaderboardRow).delete()
        db.commit()
        print("Cache table cleared successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error occurred while clearing cache table: {e}")
    finally:
        db.close()


def last_updated_at():
    db = SQLAlchemySession()
    try:
        metadata = db.query(Metadata).order_by(Metadata.timestamp.desc()).first()
        return metadata.timestamp if metadata else None
    finally:
        db.close()


def get_player_count():
    db = SQLAlchemySession()
    try:
        metadata = db.query(Metadata).order_by(Metadata.timestamp.desc()).first()
        return metadata.player_count if metadata else None
    finally:
        db.close()
