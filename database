import sqlite3
import logging
from datetime import date, datetime
from contextlib import contextmanager
from config import DB_PATH

logger = logging.getLogger(__name__)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                first_name  TEXT,
                join_date   TEXT NOT NULL,
                is_premium  INTEGER NOT NULL DEFAULT 0,
                is_banned   INTEGER NOT NULL DEFAULT 0,
                files_today INTEGER NOT NULL DEFAULT 0,
                last_reset  TEXT NOT NULL,
                files_total INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS stats (
                id              INTEGER PRIMARY KEY CHECK (id = 1),
                total_files     INTEGER NOT NULL DEFAULT 0,
                premium_users   INTEGER NOT NULL DEFAULT 0,
                today_activity  INTEGER NOT NULL DEFAULT 0,
                last_reset      TEXT NOT NULL
            );

            INSERT OR IGNORE INTO stats (id, total_files, premium_users, today_activity, last_reset)
            VALUES (1, 0, 0, 0, date('now'));
        """)
    logger.info("Database initialised.")


def _reset_daily_if_needed(conn, row: sqlite3.Row) -> dict:
    today = date.today().isoformat()
    if row["last_reset"] != today:
        conn.execute(
            "UPDATE users SET files_today=0, last_reset=? WHERE user_id=?",
            (today, row["user_id"]),
        )
        return dict(row) | {"files_today": 0, "last_reset": today}
    return dict(row)


def get_or_create_user(user_id: int, username: str | None, first_name: str | None) -> dict:
    today = date.today().isoformat()
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        if row is None:
            conn.execute(
                """INSERT INTO users
                   (user_id, username, first_name, join_date, last_reset)
                   VALUES (?,?,?,?,?)""",
                (user_id, username, first_name, today, today),
            )
            row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        else:
            conn.execute(
                "UPDATE users SET username=?, first_name=? WHERE user_id=?",
                (username, first_name, user_id),
            )
        return _reset_daily_if_needed(conn, row)


def get_user(user_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        if row is None:
            return None
        return _reset_daily_if_needed(conn, row)


def increment_user_files(user_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET files_today=files_today+1, files_total=files_total+1 WHERE user_id=?",
            (user_id,),
        )
        conn.execute(
            "UPDATE stats SET total_files=total_files+1, today_activity=today_activity+1 WHERE id=1"
        )


def set_premium(user_id: int, value: bool):
    with get_conn() as conn:
        conn.execute("UPDATE users SET is_premium=? WHERE user_id=?", (int(value), user_id))
        delta = 1 if value else -1
        conn.execute("UPDATE stats SET premium_users=MAX(0,premium_users+?) WHERE id=1", (delta,))


def set_banned(user_id: int, value: bool):
    with get_conn() as conn:
        conn.execute("UPDATE users SET is_banned=? WHERE user_id=?", (int(value), user_id))


def get_stats() -> dict:
    today = date.today().isoformat()
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM stats WHERE id=1").fetchone()
        if row["last_reset"] != today:
            conn.execute("UPDATE stats SET today_activity=0, last_reset=? WHERE id=1", (today,))
            row = conn.execute("SELECT * FROM stats WHERE id=1").fetchone()
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        premium_users = conn.execute("SELECT COUNT(*) FROM users WHERE is_premium=1").fetchone()[0]
        return {
            "total_users": total_users,
            "total_files": row["total_files"],
            "premium_users": premium_users,
            "today_activity": row["today_activity"],
        }


def get_all_user_ids() -> list[int]:
    with get_conn() as conn:
        rows = conn.execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()
        return [r["user_id"] for r in rows]
