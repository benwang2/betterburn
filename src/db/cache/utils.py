import csv
from datetime import datetime, timezone

from ...constants import Rank
from ...custom_logger import CustomLogger
from ..database import SQLAlchemySession
from .models import LeaderboardRow, Metadata

logger = CustomLogger("cache_utils")


def update_metadata(num_rows):
    db = SQLAlchemySession()

    try:
        timestamp = datetime.now(timezone.utc).timestamp()

        db.query(Metadata).delete()
        metadata_entry = Metadata(updated=timestamp, player_count=num_rows)
        db.add(metadata_entry)
        db.commit()
    finally:
        db.close()


def get_rank_data_by_steam_id(steam_id):
    db = SQLAlchemySession()
    try:
        record = db.query(LeaderboardRow).filter_by(steam_id=steam_id).first()
        return record if record else None
    finally:
        db.close()


def get_rank_from_values(score: int, position: int) -> Rank:
    rank: Rank = Rank.Stone

    if score >= 500 and score < 700:
        rank = Rank.Bronze
    elif score >= 700 and score < 900:
        rank = Rank.Silver
    elif score >= 900 and score < 1100:
        rank = Rank.Gold
    elif score >= 1100 and score < 1300:
        rank = Rank.Platinum
    elif score >= 1300 and score < 1500:
        rank = Rank.Diamond
    elif score >= 1500 and score < 1700:
        rank = Rank.Master
    elif score >= 1700:
        rank = Rank.Grandmaster
        if score >= 1800 and position <= 100:
            rank = Rank.Aetherean

    return rank


def get_rank_from_row(row: LeaderboardRow) -> Rank:
    if row is None:
        return Rank.Stone

    return get_rank_from_values(row.score, row.rank)


def bulk_insert_cache_from_list(leaderboard: list):
    """
    Bulk inserts records into the 'cache' table from a list.

    The file should have headers describing the columns.
    The index of the row (0-based) will be used as the 'rank'.

    Args:
        leaderboard (List<Dict>)
    """
    db = SQLAlchemySession()
    try:
        records = []

        for steam_id, data in leaderboard:
            steam_id = int(steam_id)
            score = int(data.get("score"))
            rank = int(data.get("rank"))
            records.append(LeaderboardRow(steam_id=steam_id, score=score, rank=rank))

        # Bulk insert using SQLAlchemy

        # Update metadata table with current timestamp and player count

        db.bulk_save_objects(records)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error occurred during bulk insert: {e}")
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
    try:
        records = []
        with open(file_path, "r") as file:
            reader = csv.DictReader(file)  # Automatically uses headers as keys
            for _, row in enumerate(reader, start=1):  # Start rank at 1
                # Parse and create a LeaderboardRow object
                steam_id = int(row.get("steam_id"))
                score = int(row.get("score"))
                rank = int(row.get("rank"))
                records.append(LeaderboardRow(steam_id=steam_id, score=score, rank=rank))

        # Bulk insert using SQLAlchemy

        # Update metadata table with current timestamp and player count

        db.bulk_save_objects(records)
        db.commit()
        logger.info(f"Successfully inserted {len(records)} records into the 'cache' table.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error occurred during bulk insert: {e}")
    finally:
        db.close()


def clear_cache_table():
    db = SQLAlchemySession()
    try:
        db.query(LeaderboardRow).delete()
        db.commit()
        logger.info("Cache table cleared successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error occurred while clearing cache table: {e}")
    finally:
        db.close()


def last_updated_at():
    db = SQLAlchemySession()
    try:
        # Since update_metadata() clears the table first, we expect a single row.
        metadata = db.query(Metadata).first()
        return metadata.updated if metadata else None
    finally:
        db.close()


def get_player_count():
    db = SQLAlchemySession()
    try:
        metadata = db.query(Metadata).first()
        return metadata.player_count if metadata else None
    finally:
        db.close()
