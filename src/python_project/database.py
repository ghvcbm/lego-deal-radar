"""SQLite persistence for Architecture sets and marketplace listings."""

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


@dataclass(frozen=True)
class ListingRecord:
    """A marketplace listing stored in SQLite."""

    id: str
    marketplace: str
    title: str
    price: float
    url: str
    image_url: str | None = None
    seller_name: str | None = None
    description: str | None = None
    score: float | None = None


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

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS listings (
            id TEXT NOT NULL,
            marketplace TEXT NOT NULL,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            url TEXT NOT NULL,
            image_url TEXT,
            seller_name TEXT,
            description TEXT,
            score REAL,
            first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (marketplace, id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS listings (
            id TEXT NOT NULL,
            marketplace TEXT NOT NULL,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            url TEXT NOT NULL,
            image_url TEXT,
            seller_name TEXT,
            description TEXT,
            score REAL,
            first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (marketplace, id)
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
            [
                (
                    item.set_num,
                    item.name,
                    item.year,
                    item.num_parts,
                )
                for item in records
            ],
        )

    return len(records)


def list_architecture_sets(
    connection: sqlite3.Connection,
) -> list[ArchitectureSet]:
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


def upsert_listing(
    connection: sqlite3.Connection,
    listing: ListingRecord,
) -> bool:
    """
    Insert or update a marketplace listing.

    Returns True if the listing was new, False if it already existed.
    """

    existing = connection.execute(
        """
        SELECT 1
        FROM listings
        WHERE marketplace = ? AND id = ?
        """,
        (listing.marketplace, listing.id),
    ).fetchone()

    with connection:
        connection.execute(
            """
            INSERT INTO listings (
                id,
                marketplace,
                title,
                price,
                url,
                image_url,
                seller_name,
                description,
                score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (marketplace, id)
            DO UPDATE SET
                title = excluded.title,
                price = excluded.price,
                url = excluded.url,
                image_url = excluded.image_url,
                seller_name = excluded.seller_name,
                description = excluded.description,
                score = excluded.score,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                listing.id,
                listing.marketplace,
                listing.title,
                listing.price,
                listing.url,
                listing.image_url,
                listing.seller_name,
                listing.description,
                listing.score,
            ),
        )

    return existing is None
