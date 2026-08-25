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
    """Create all required database tables."""

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS architecture_sets (
            set_num TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            year INTEGER NOT NULL,
            theme_id INTEGER,
            num_parts INTEGER NOT NULL,
            set_img_url TEXT,
            set_url TEXT,
            last_modified_dt TEXT
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (marketplace, id)
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS listing_price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id TEXT NOT NULL,
            marketplace TEXT NOT NULL,
            price REAL NOT NULL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_listing_price_history_listing
        ON listing_price_history (marketplace, listing_id)
        """
    )

    connection.commit()


def upsert_listing(
    connection: sqlite3.Connection,
    listing: ListingRecord,
) -> bool:
    """Insert or update a listing.

    Returns True when the listing is seen for the first time.
    """

    existing = connection.execute(
        """
        SELECT 1
        FROM listings
        WHERE marketplace = ? AND id = ?
        """,
        (
            listing.marketplace,
            listing.id,
        ),
    ).fetchone()

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

    connection.commit()

    return existing is None


def save_listings(
    connection: sqlite3.Connection,
    listings: Iterable[ListingRecord],
) -> list[ListingRecord]:
    """Save listings and return only listings seen for the first time."""

    new_listings: list[ListingRecord] = []

    for listing in listings:
        if upsert_listing(connection, listing):
            new_listings.append(listing)

        record_price_history(connection, listing)

    return new_listings


def record_price_history(
    connection: sqlite3.Connection,
    listing: ListingRecord,
) -> None:
    """Record the listing price when it changes."""

    last = connection.execute(
        """
        SELECT price
        FROM listing_price_history
        WHERE marketplace = ?
          AND listing_id = ?
        ORDER BY recorded_at DESC
        LIMIT 1
        """,
        (
            listing.marketplace,
            listing.id,
        ),
    ).fetchone()

    if last is not None and float(last["price"]) == float(listing.price):
        return

    connection.execute(
        """
        INSERT INTO listing_price_history (
            listing_id,
            marketplace,
            price
        )
        VALUES (?, ?, ?)
        """,
        (
            listing.id,
            listing.marketplace,
            listing.price,
        ),
    )

    connection.commit()
