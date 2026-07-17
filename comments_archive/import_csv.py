import csv
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIRECTORY = Path(__file__).resolve().parent
PROJECT_DIRECTORY = SCRIPT_DIRECTORY.parent
sys.path.insert(0, str(PROJECT_DIRECTORY))

from database import import_archived_comments


CSV_PATH = SCRIPT_DIRECTORY / "comments.csv"


def import_comments(csv_path=CSV_PATH):
    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    required_fields = {"source_key", "name", "comment", "created_at"}
    if rows and not required_fields.issubset(rows[0]):
        missing = ", ".join(sorted(required_fields - rows[0].keys()))
        raise ValueError(f"CSV is missing required fields: {missing}")

    for row in rows:
        datetime.fromisoformat(row["created_at"])

    inserted = import_archived_comments(rows)
    print(f"Imported {inserted} new comments from {csv_path} ({len(rows)} rows read).")
    if inserted < len(rows):
        print(f"Skipped {len(rows) - inserted} comments that were already imported.")
    return inserted


if __name__ == "__main__":
    import_comments()
