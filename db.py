import sqlite3
import os
import json
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "users.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                plan TEXT NOT NULL DEFAULT 'free'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                name TEXT NOT NULL,
                industry TEXT,
                website_quality TEXT,
                score INTEGER,
                reason TEXT,
                address TEXT,
                status TEXT NOT NULL DEFAULT 'new',
                notes TEXT NOT NULL DEFAULT '',
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        """)
        conn.commit()
    _migrate_from_json()


def _migrate_from_json():
    if not os.path.exists("users.json"):
        return
    try:
        with open("users.json") as f:
            data = json.load(f)
        with _connect() as conn:
            for username, info in data.items():
                password = info.get("password", "")
                plan = info.get("plan", "free")
                if not password.startswith("$2b$"):
                    logger.warning("Skipping user '%s': invalid password hash", username)
                    continue
                conn.execute(
                    "INSERT OR IGNORE INTO users (username, password, plan) VALUES (?, ?, ?)",
                    (username, password, plan),
                )
            conn.commit()
        os.rename("users.json", "users.json.bak")
        logger.info("Migrated users.json -> users.db (backup: users.json.bak)")
    except Exception:
        logger.exception("Migration from users.json failed")


def get_user(username: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None


def user_exists(username: str) -> bool:
    return get_user(username) is not None


def create_user(username: str, hashed_password: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO users (username, password, plan) VALUES (?, ?, 'free')",
            (username, hashed_password),
        )
        conn.commit()


def get_user_plan(username: str) -> str:
    user = get_user(username)
    return user["plan"] if user else "free"


def set_user_plan(username: str, plan: str) -> bool:
    with _connect() as conn:
        cursor = conn.execute(
            "UPDATE users SET plan = ? WHERE username = ?", (plan, username)
        )
        conn.commit()
        return cursor.rowcount > 0


_ALLOWED_STATUSES = {"new", "contacted", "done"}


def save_lead(username: str, lead: dict) -> int:
    with _connect() as conn:
        cursor = conn.execute(
            """INSERT INTO saved_leads (username, name, industry, website_quality, score, reason, address)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                username,
                str(lead.get("name", ""))[:200],
                str(lead.get("industry", ""))[:200],
                str(lead.get("website_quality", ""))[:50],
                int(lead.get("score", 0)),
                str(lead.get("reason", ""))[:500],
                str(lead.get("address", ""))[:300],
            ),
        )
        conn.commit()
        return cursor.lastrowid


def get_saved_leads(username: str) -> list:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM saved_leads WHERE username = ? ORDER BY saved_at DESC",
            (username,),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_saved_lead(lead_id: int, username: str) -> bool:
    with _connect() as conn:
        cursor = conn.execute(
            "DELETE FROM saved_leads WHERE id = ? AND username = ?",
            (lead_id, username),
        )
        conn.commit()
        return cursor.rowcount > 0


def update_saved_lead(lead_id: int, username: str, status: str | None, notes: str | None) -> bool:
    if status is not None and status not in _ALLOWED_STATUSES:
        return False
    with _connect() as conn:
        if status is not None and notes is not None:
            cursor = conn.execute(
                "UPDATE saved_leads SET status = ?, notes = ? WHERE id = ? AND username = ?",
                (status, notes[:1000], lead_id, username),
            )
        elif status is not None:
            cursor = conn.execute(
                "UPDATE saved_leads SET status = ? WHERE id = ? AND username = ?",
                (status, lead_id, username),
            )
        elif notes is not None:
            cursor = conn.execute(
                "UPDATE saved_leads SET notes = ? WHERE id = ? AND username = ?",
                (notes[:1000], lead_id, username),
            )
        else:
            return False
        conn.commit()
        return cursor.rowcount > 0


def is_lead_saved(username: str, name: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM saved_leads WHERE username = ? AND name = ?",
            (username, name),
        ).fetchone()
        return row is not None