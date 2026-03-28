import sqlite3
from datetime import datetime

DB_PATH = "tasq_agent.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS seen_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                company TEXT,
                first_seen_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                company TEXT,
                location TEXT,
                fit_score INTEGER,
                status TEXT DEFAULT 'applied',
                applied_at TEXT NOT NULL,
                last_updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS token_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                tokens_used INTEGER NOT NULL DEFAULT 0
            );
        """)


# --- Seen jobs (dedup) ---

def is_job_seen(url: str) -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT 1 FROM seen_jobs WHERE url = ?", (url,)).fetchone()
        return row is not None


def mark_job_seen(url: str, title: str = None, company: str = None):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO seen_jobs (url, title, company, first_seen_at) VALUES (?, ?, ?, ?)",
            (url, title, company, datetime.utcnow().isoformat()),
        )


# --- Application tracking ---

def save_application(url: str, title: str, company: str, location: str, fit_score: int):
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO applications (url, title, company, location, fit_score, status, applied_at, last_updated_at)
               VALUES (?, ?, ?, ?, ?, 'applied', ?, ?)
               ON CONFLICT(url) DO UPDATE SET
                   status = 'applied',
                   last_updated_at = excluded.last_updated_at""",
            (url, title, company, location, fit_score, now, now),
        )


def get_all_applications():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM applications ORDER BY applied_at DESC"
        ).fetchall()


def get_stale_applications(days: int):
    with get_connection() as conn:
        return conn.execute(
            """SELECT * FROM applications
               WHERE status = 'applied'
               AND julianday('now') - julianday(last_updated_at) >= ?""",
            (days,),
        ).fetchall()


# --- Daily token tracking ---

def get_tokens_used_today() -> int:
    today = datetime.utcnow().date().isoformat()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT tokens_used FROM token_usage WHERE date = ?", (today,)
        ).fetchone()
        return row["tokens_used"] if row else 0


def increment_token_usage(tokens: int):
    today = datetime.utcnow().date().isoformat()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO token_usage (date, tokens_used) VALUES (?, ?)
               ON CONFLICT(date) DO UPDATE SET tokens_used = tokens_used + excluded.tokens_used""",
            (today, tokens),
        )


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
