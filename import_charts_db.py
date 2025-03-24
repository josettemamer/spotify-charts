"""
import_charts_db.py

Initializes a local SQLite database and imports one or more Spotify chart JSON files
from the 'weekly_data/' folder.

Schema:
- tracks (track_id, name, artist_names)
- weekly_charts (week_id, country, rank, streams, track_id)

This script is designed to be safe to re-run. Duplicate chart entries are ignored
based on a unique (week_id, country, track_id) constraint.
"""

import os
import json
import sqlite3
import logging
from pathlib import Path
import argparse

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DB_FILE = "spotify_charts.db"
DATA_DIR = Path("weekly_data")
DATA_DIR.mkdir(exist_ok=True)


def initialize_db():
    """Create the SQLite schema with deduplication for weekly_charts."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tracks (
                track_id TEXT PRIMARY KEY,
                track_name TEXT NOT NULL,
                artist_names TEXT NOT NULL
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_charts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_id TEXT NOT NULL,
                country TEXT NOT NULL,
                rank INTEGER NOT NULL,
                streams INTEGER NOT NULL,
                track_id TEXT NOT NULL,
                FOREIGN KEY (track_id) REFERENCES tracks(track_id),
                UNIQUE (week_id, country, track_id)
            );
        """)

        conn.commit()
        logger.info("Database initialized.")


def insert_weekly_data(json_file: Path) -> int:
    """
    Insert track metadata and weekly chart entries into the database.
    
    Returns:
        int: Number of new weekly chart rows inserted.
    """
    inserted = 0

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        with json_file.open("r", encoding="utf-8") as f:
            weekly_data = json.load(f)

        for entry in weekly_data:
            track_id = entry["track_id"]
            track_name = entry["track_name"]
            artist_names = json.dumps(entry["artist_names"])

            cursor.execute("""
                INSERT OR IGNORE INTO tracks (track_id, track_name, artist_names)
                VALUES (?, ?, ?);
            """, (track_id, track_name, artist_names))

            cursor.execute("""
                INSERT OR IGNORE INTO weekly_charts (week_id, country, rank, streams, track_id)
                VALUES (?, ?, ?, ?, ?);
            """, (entry["week_id"], entry["country"], entry["rank"], entry["streams"], track_id))

            inserted += cursor.rowcount  # 1 if new row inserted, 0 if ignored

        conn.commit()

    return inserted


def run():
    parser = argparse.ArgumentParser(description="Import Spotify chart JSON into SQLite.")
    parser.add_argument("--file", type=str, help="Path to a specific weekly_charts_*.json file")
    parser.add_argument("--all", action="store_true", help="Process all available weekly JSON files")
    args = parser.parse_args()

    initialize_db()

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return
        count = insert_weekly_data(file_path)
        if count:
            logger.info(f"Inserted {count} new entries from {file_path.name}")
        else:
            logger.info(f"No new entries inserted from {file_path.name} (already in database)")

    else:
        json_files = sorted(DATA_DIR.glob("weekly_charts_*.json"))
        if not json_files:
            logger.warning("No weekly chart JSON files found.")
            return

        logger.info(f"Processing {len(json_files)} files...")
        for file in json_files:
            count = insert_weekly_data(file)
            if count:
                logger.info(f"Inserted {count} new entries from {file.name}")
            else:
                logger.info(f"No new entries inserted from {file.name} (already in database)")


if __name__ == "__main__":
    run()
