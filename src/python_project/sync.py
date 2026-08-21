"""Synchronize Rebrickable Architecture sets into SQLite."""

from __future__ import annotations

from collections.abc import Callable
import sqlite3

from .database import ArchitectureSet, connect, replace_architecture_sets
from .rebrickable import RebrickableClient


def sync_architecture(
    db_path: str | None = None,
    client: RebrickableClient | None = None,
    connection_factory: Callable[[str | None], sqlite3.Connection] = connect,
) -> int:
    """Fetch all Architecture sets and replace the local catalog."""
    api_client = client or RebrickableClient()
    raw_sets = api_client.get_architecture_sets()
    required_fields = ("set_num", "name", "year", "num_parts")
    normalized: list[ArchitectureSet] = []
    for item in raw_sets:
        if not all(key in item for key in required_fields):
            raise ValueError("Rebrickable returned an Architecture set with missing fields.")
        normalized.append(
            ArchitectureSet(
                set_num=str(item["set_num"]),
                name=str(item["name"]),
                year=int(item["year"]),
                num_parts=int(item["num_parts"]),
            )
        )
    connection = connection_factory(db_path)
    try:
        return replace_architecture_sets(connection, normalized)
    finally:
        connection.close()