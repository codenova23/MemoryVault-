"""SQLite persistence for Memory Vault."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterator


DEFAULT_DB_PATH = Path(__file__).parent / "data" / "memory_vault.sqlite3"

DEMO_MEMORIES = [
    {
        "id": "demo-goa",
        "title": "A little Goa escape",
        "date": "2026-08-14",
        "location": "Goa, India",
        "description": "Salt in our hair, nowhere to be, and one more sunset before we left.",
        "category": "Travel",
        "tags": ["Travel", "Friends", "Beach", "Summer", "Sunset"],
        "people": ["Maya", "Dev", "Aanya"],
        "favorite": True,
        "photo_url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=85",
        "caption": "That last golden hour",
        "time": "5:42 PM",
    },
    {
        "id": "demo-college",
        "title": "College, lately",
        "date": "2026-09-18",
        "location": "Pune, India",
        "description": "Coffee runs, borrowed notes, and the people who made it feel like home.",
        "category": "College",
        "tags": ["College", "Friends", "Everyday"],
        "people": ["The usual crew"],
        "favorite": False,
        "photo_url": "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?auto=format&fit=crop&w=1200&q=85",
        "caption": "The usual crew",
        "time": "11:20 AM",
    },
    {
        "id": "demo-birthday",
        "title": "A birthday in full color",
        "date": "2026-07-20",
        "location": "Mumbai, India",
        "description": "A tiny cake, a very loud room, and the best kind of happy tears.",
        "category": "Celebrations",
        "tags": ["Celebration", "Friends", "Birthday"],
        "people": ["Nina and the gang"],
        "favorite": True,
        "photo_url": "https://images.unsplash.com/photo-1511795409834-ef04bbd61622?auto=format&fit=crop&w=1200&q=85",
        "caption": "Make a wish",
        "time": "8:30 PM",
    },
    {
        "id": "demo-family",
        "title": "Sunday at home",
        "date": "2026-06-07",
        "location": "Jaipur, India",
        "description": "Everyone around the table, telling the same stories all over again.",
        "category": "Family",
        "tags": ["Family", "Food", "Home"],
        "people": ["All of us"],
        "favorite": False,
        "photo_url": "https://images.unsplash.com/photo-1511895426328-dc8714191300?auto=format&fit=crop&w=1200&q=85",
        "caption": "All together again",
        "time": "12:30 PM",
    },
    {
        "id": "demo-sunset",
        "title": "The long way home",
        "date": "2024-10-07",
        "location": "Marine Drive, Mumbai",
        "description": "We stopped for five minutes. The sky had other plans.",
        "category": "Nature",
        "tags": ["Nature", "Sunset", "Friends", "Evening"],
        "people": ["Maya"],
        "favorite": True,
        "photo_url": "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?auto=format&fit=crop&w=1200&q=85",
        "caption": "Five more minutes",
        "time": "5:42 PM",
    },
]


def database_path() -> Path:
    configured = os.environ.get("MEMORY_VAULT_DB")
    path = Path(configured).expanduser() if configured else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(database_path(), timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database() -> None:
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                memory_date TEXT NOT NULL,
                location TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL,
                tags_json TEXT NOT NULL DEFAULT '[]',
                people_json TEXT NOT NULL DEFAULT '[]',
                favorite INTEGER NOT NULL DEFAULT 0,
                is_demo INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id TEXT NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
                photo_data BLOB,
                photo_url TEXT NOT NULL DEFAULT '',
                caption TEXT NOT NULL DEFAULT '',
                captured_at TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS capsules (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                unlock_date TEXT NOT NULL,
                memory_id TEXT REFERENCES memories(id) ON DELETE SET NULL,
                cover_data BLOB,
                cover_url TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_memories_date ON memories(memory_date);
            CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
            CREATE INDEX IF NOT EXISTS idx_photos_memory ON photos(memory_id);
            CREATE INDEX IF NOT EXISTS idx_capsules_unlock ON capsules(unlock_date);
            """
        )
        seeded = connection.execute(
            "SELECT value FROM settings WHERE key = 'demo_seeded'"
        ).fetchone()
        if not seeded:
            _insert_demo_memories(connection)
            connection.execute(
                "INSERT INTO settings (key, value) VALUES ('demo_seeded', '1')"
            )


def _insert_demo_memories(connection: sqlite3.Connection) -> None:
    for memory in DEMO_MEMORIES:
        connection.execute(
            """INSERT OR IGNORE INTO memories
            (id, title, memory_date, location, description, category, tags_json,
             people_json, favorite, is_demo, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
            (
                memory["id"],
                memory["title"],
                memory["date"],
                memory["location"],
                memory["description"],
                memory["category"],
                json.dumps(memory["tags"]),
                json.dumps(memory["people"]),
                int(memory["favorite"]),
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
        connection.execute(
            """INSERT INTO photos (memory_id, photo_url, caption, captured_at)
            SELECT ?, ?, ?, ? WHERE NOT EXISTS
            (SELECT 1 FROM photos WHERE memory_id = ?)""",
            (
                memory["id"],
                memory["photo_url"],
                memory["caption"],
                memory["time"],
                memory["id"],
            ),
        )


def restore_demo_memories() -> None:
    with connect() as connection:
        _insert_demo_memories(connection)
        connection.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('demo_seeded', '1')"
        )


def remove_demo_memories() -> int:
    with connect() as connection:
        cursor = connection.execute("DELETE FROM memories WHERE is_demo = 1")
        return cursor.rowcount


def _decode_memory(row: sqlite3.Row, include_photos: bool = True) -> dict[str, Any]:
    memory = dict(row)
    memory["date"] = memory.pop("memory_date")
    memory["tags"] = json.loads(memory.pop("tags_json") or "[]")
    memory["people"] = json.loads(memory.pop("people_json") or "[]")
    memory["favorite"] = bool(memory["favorite"])
    memory["is_demo"] = bool(memory["is_demo"])
    if include_photos:
        with connect() as connection:
            photos = connection.execute(
                "SELECT id, photo_data, photo_url, caption, captured_at "
                "FROM photos WHERE memory_id = ? ORDER BY id",
                (memory["id"],),
            ).fetchall()
        memory["photos"] = [dict(photo) for photo in photos]
    else:
        memory["photos"] = []
    return memory


def list_memories(
    category: str | None = None,
    favorites_only: bool = False,
    search: str = "",
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if category and category != "All memories":
        clauses.append("(category = ? OR tags_json LIKE ?)")
        params.extend((category, f'%"{category}"%'))
    if favorites_only:
        clauses.append("favorite = 1")
    normalized_search = search.strip().lower()
    if normalized_search:
        clauses.append(
            "(lower(title) LIKE ? OR lower(location) LIKE ? OR lower(description) LIKE ? "
            "OR lower(tags_json) LIKE ? OR lower(people_json) LIKE ? OR memory_date LIKE ?)"
        )
        wildcard = f"%{normalized_search}%"
        params.extend([wildcard] * 5 + [wildcard])
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with connect() as connection:
        rows = connection.execute(
            f"SELECT * FROM memories {where} ORDER BY memory_date DESC, created_at DESC",
            params,
        ).fetchall()
    return [_decode_memory(row) for row in rows]


def get_memory(memory_id: str) -> dict[str, Any] | None:
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()
    return _decode_memory(row) if row else None


def create_memory(
    *,
    title: str,
    memory_date: date,
    location: str,
    description: str,
    category: str,
    tags: list[str],
    people: list[str],
    favorite: bool,
    photos: list[dict[str, Any]],
) -> str:
    memory_id = f"memory-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with connect() as connection:
        connection.execute(
            """INSERT INTO memories
            (id, title, memory_date, location, description, category, tags_json,
             people_json, favorite, is_demo, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)""",
            (
                memory_id,
                title,
                memory_date.isoformat(),
                location,
                description,
                category,
                json.dumps(tags),
                json.dumps(people),
                int(favorite),
                created_at,
            ),
        )
        connection.executemany(
            """INSERT INTO photos (memory_id, photo_data, photo_url, caption, captured_at)
            VALUES (?, ?, '', ?, ?)""",
            [
                (memory_id, photo.get("data"), photo.get("caption", "A saved moment"), photo.get("time", ""))
                for photo in photos
            ],
        )
    return memory_id


def set_favorite(memory_id: str, favorite: bool) -> None:
    with connect() as connection:
        connection.execute(
            "UPDATE memories SET favorite = ? WHERE id = ?",
            (int(favorite), memory_id),
        )


def delete_memory(memory_id: str) -> None:
    with connect() as connection:
        connection.execute("DELETE FROM memories WHERE id = ?", (memory_id,))


def create_capsule(
    *, title: str, message: str, unlock_date: date, memory_id: str | None
) -> str:
    capsule_id = f"capsule-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    cover_data = None
    cover_url = ""
    if memory_id:
        with connect() as connection:
            photo = connection.execute(
                "SELECT photo_data, photo_url FROM photos "
                "WHERE memory_id = ? ORDER BY id LIMIT 1",
                (memory_id,),
            ).fetchone()
        if photo:
            cover_data, cover_url = photo["photo_data"], photo["photo_url"]
    with connect() as connection:
        connection.execute(
            """INSERT INTO capsules
            (id, title, message, unlock_date, memory_id, cover_data, cover_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                capsule_id,
                title,
                message,
                unlock_date.isoformat(),
                memory_id,
                cover_data,
                cover_url,
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
    return capsule_id


def list_capsules() -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(
            "SELECT * FROM capsules ORDER BY unlock_date ASC, created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def delete_capsule(capsule_id: str) -> None:
    with connect() as connection:
        connection.execute("DELETE FROM capsules WHERE id = ?", (capsule_id,))


def clear_all_data() -> None:
    with connect() as connection:
        connection.execute("DELETE FROM capsules")
        connection.execute("DELETE FROM memories")
        connection.execute("DELETE FROM settings WHERE key = 'generated_story'")
        connection.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('demo_seeded', '1')"
        )


def get_setting(key: str) -> str | None:
    with connect() as connection:
        row = connection.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
    return row["value"] if row else None


def set_setting(key: str, value: str) -> None:
    with connect() as connection:
        connection.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
