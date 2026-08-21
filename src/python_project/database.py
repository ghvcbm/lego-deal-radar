"""SQLite persistence for Architecture sets."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


DEFAULT_DATABASE_PATH = "architecture_sets.sqlite3"


@dataclass(frozen=True)
class ArchitectureSet:
    """The set fields displayed by the bot."""

    set_num: str
    name: str
    year: int
    num_parts: int


def database_path() -> str:
    """Return the configured SQLite path, or a local default."""
    return os.environ.get("SQLITE_DB_PATH", DEFAULT_DATABASE_PATH)


def connect(path: str | None = None) -> sqlite3.Connection:
    """Open and initialize the SQLite database."""
    resolved_path = path or database_path()
    parent = Path(resolved_path).expanduser().parent
    if str(parent) not in ("", "."):
        parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(resolved_path)
    connection.row_factory = sqlite3.Row
    initialize(connection)
    return connection


def initialize(connection: sqlite3.Connection) -> None:
    """Create the database schema if it does not exist."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS architecture_sets (
            set_num TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            year INTEGER NOT NULL,
            num_parts INTEGER NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.commit()


def replace_architecture_sets(
    connection: sqlite3.Connection,
    sets: Iterable[ArchitectureSet],
) -> int:
    """Replace the stored Architecture catalog atomically."""
    records = list(sets)
    with connection:
        connection.execute("DELETE FROM architecture_sets")
        connection.executemany(
            """
            INSERT INTO architecture_sets (set_num, name, year, num_parts)
            VALUES (?, ?, ?, ?)
            """,
            [(item.set_num, item.name, item.year, item.num_parts) for item in records],
        )
    return len(records)


def list_architecture_sets(connection: sqlite3.Connection) -> list[ArchitectureSet]:
    """Return stored sets in a useful display order."""
    rows = connection.execute(
        """
        SELECT set_num, name, year, num_parts
        FROM architecture_sets
        ORDER BY year DESC, name COLLATE NOCASE ASC, set_num ASC
        """
    ).fetchall()
    return [
        ArchitectureSet(
            set_num=row["set_num"],
            name=row["name"],
            year=row["year"],
            num_parts=row["num_parts"],
        )
        for row in rows
    ]