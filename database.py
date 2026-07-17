import sqlite3
from datetime import datetime
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "portal.db"


def initialize_database():
    with sqlite3.connect(DATABASE_PATH) as database:
        database.execute(
            """
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER NOT NULL,
                option_index INTEGER NOT NULL,
                submitter_ip TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        vote_columns = {
            row[1] for row in database.execute("PRAGMA table_info(votes)")
        }
        if "submitter_ip" not in vote_columns:
            database.execute("ALTER TABLE votes ADD COLUMN submitter_ip TEXT")
        database.execute(
            "CREATE INDEX IF NOT EXISTS votes_poll_id ON votes (poll_id)"
        )
        database.execute(
            """
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                comment TEXT NOT NULL,
                submitter_ip TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        database.execute(
            "CREATE INDEX IF NOT EXISTS comments_created_at ON comments (created_at DESC, id DESC)"
        )
        comment_columns = {
            row[1] for row in database.execute("PRAGMA table_info(comments)")
        }
        if "source_key" not in comment_columns:
            database.execute("ALTER TABLE comments ADD COLUMN source_key TEXT")
        database.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS comments_source_key
            ON comments (source_key)
            WHERE source_key IS NOT NULL
            """
        )


def record_vote(poll_id, option_index, submitter_ip):
    with sqlite3.connect(DATABASE_PATH) as database:
        database.execute(
            """
            INSERT INTO votes (poll_id, option_index, submitter_ip)
            VALUES (?, ?, ?)
            """,
            (poll_id, option_index, submitter_ip),
        )


def get_vote_counts(poll_id, option_count):
    vote_counts = [0] * option_count
    with sqlite3.connect(DATABASE_PATH) as database:
        rows = database.execute(
            """
            SELECT option_index, COUNT(*)
            FROM votes
            WHERE poll_id = ?
            GROUP BY option_index
            """,
            (poll_id,),
        )
        for option_index, count in rows:
            if 0 <= option_index < option_count:
                vote_counts[option_index] = count
    return vote_counts


def record_comment(name, comment, submitter_ip):
    with sqlite3.connect(DATABASE_PATH) as database:
        database.execute(
            """
            INSERT INTO comments (name, comment, submitter_ip)
            VALUES (?, ?, ?)
            """,
            (name, comment, submitter_ip),
        )


def import_archived_comments(comments):
    rows = [
        (
            entry["name"],
            entry["comment"],
            entry["created_at"],
            entry["source_key"],
        )
        for entry in comments
    ]
    with sqlite3.connect(DATABASE_PATH) as database:
        before = database.total_changes
        database.executemany(
            """
            INSERT OR IGNORE INTO comments
                (name, comment, created_at, source_key)
            VALUES (?, ?, ?, ?)
            """,
            rows,
        )
        return database.total_changes - before


def get_comments(page, per_page=10):
    offset = (page - 1) * per_page
    with sqlite3.connect(DATABASE_PATH) as database:
        database.row_factory = sqlite3.Row
        total = database.execute("SELECT COUNT(*) FROM comments").fetchone()[0]
        rows = database.execute(
            """
            SELECT name, comment, created_at
            FROM comments
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (per_page, offset),
        ).fetchall()

    comments = []
    for row in rows:
        created_at = datetime.fromisoformat(row["created_at"])
        posttime = created_at.strftime("%I:%M %p on %B %d, %Y")
        posttime = posttime.lstrip("0").replace(" 0", " ")
        comments.append(
            {
                "name": row["name"],
                "comment": row["comment"],
                "posttime": posttime,
            }
        )
    return comments, total


initialize_database()
