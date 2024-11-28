import csv
import datetime

from ..database import Session
from .models import LeaderboardRow, Metadata


# Insert example data into the cache table
def _insert_example_data():
    session = Session()
    try:
        cache_entries = [
            LeaderboardRow(steam_id=12345, score=100, rank=1),
            LeaderboardRow(steam_id=67890, score=200, rank=2),
        ]
        session.add_all(cache_entries)
        session.commit()
    finally:
        session.close()


# Query example data from the cache table
def _query_example_data():
    session = Session()
    try:
        cache_data = session.query(LeaderboardRow).all()
        print("Cache Table:")
        for entry in cache_data[:10]:
            print(
                f"Steam ID: {entry.steam_id}, Score: {entry.score}, Rank: {entry.rank}"
            )
        print("...")
    finally:
        session.close()


def update_metadata(num_rows):
    session = Session()

    try:
        timestamp = datetime.now()

        session.query(Metadata).delete()
        metadata_entry = Metadata(timestamp=timestamp, player_count=num_rows)
        session.add(metadata_entry)
    finally:
        session.close()


# Get score by Steam ID
def get_score_by_steam_id(steam_id):
    session = Session()
    try:
        record = session.query(LeaderboardRow).filter_by(steam_id=steam_id).first()
        return record.score if record else None
    finally:
        session.close()


def bulk_insert_cache_from_file(file_path):
    """
    Bulk inserts records into the 'cache' table from a CSV file.

    The file should have headers describing the columns.
    The index of the row (0-based) will be used as the 'rank'.

    Args:
        file_path (str): Path to the input CSV file.
    """
    session = Session()
    # print("Hi", file_path)
    try:
        records = []
        with open(file_path, "r") as file:
            # print(file.readline())
            reader = csv.DictReader(file)  # Automatically uses headers as keys
            for _, row in enumerate(reader, start=1):  # Start rank at 1
                # Parse and create a LeaderboardRow object
                # print(row)
                steam_id = int(row.get("steam_id"))
                score = int(row.get("score"))
                rank = int(row.get("rank"))
                # print(steam_id, score, rank)
                records.append(
                    LeaderboardRow(steam_id=steam_id, score=score, rank=rank)
                )

        # Bulk insert using SQLAlchemy

        # Update metadata table with current timestamp and player count

        session.bulk_save_objects(records)
        session.commit()
        print(f"Successfully inserted {len(records)} records into the 'cache' table.")
    except Exception as e:
        session.rollback()
        print(f"Error occurred during bulk insert: {e}")
    finally:
        session.close()


def clear_cache_table():
    session = Session()
    try:
        session.query(LeaderboardRow).delete()
        session.commit()
        print("Cache table cleared successfully.")
    except Exception as e:
        session.rollback()
        print(f"Error occurred while clearing cache table: {e}")
    finally:
        session.close()
