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


def set_user_plan(username: str, plan: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET plan = ? WHERE username = ?", (plan, username)
        )
        conn.commit()