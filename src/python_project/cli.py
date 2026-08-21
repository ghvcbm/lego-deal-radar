"""Command-line entry point for the Rebrickable and Telegram project."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from .http import APIError
from .config import ConfigurationError
from .bot import run_polling
from .database import connect, list_architecture_sets
from .rebrickable import RebrickableClient
from .sync import sync_architecture
from .telegram import TelegramBot


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="lego-deal-radar",
        description="LEGO Deal Radar: Rebrickable catalog and Telegram bot.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    lookup = commands.add_parser("lookup-set", help="look up one Rebrickable set")
    lookup.add_argument("set_number", help="Rebrickable set number")

    search = commands.add_parser("search-sets", help="search Rebrickable sets")
    search.add_argument("query", help="name or number to search for")
    search.add_argument("--limit", type=int, default=10, help="maximum results")

    message = commands.add_parser("send-message", help="send a Telegram message")
    message.add_argument("chat_id", help="Telegram chat ID")
    message.add_argument("text", help="message text")

    commands.add_parser(
        "sync",
        help='find the exact "Architecture" theme and store all its sets in SQLite',
    )
    commands.add_parser("bot", help="start the Telegram polling bot")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command-line application."""
    args = build_parser().parse_args(argv)

    try:
        if args.command == "lookup-set":
            result = RebrickableClient().get_set(args.set_number)
        elif args.command == "search-sets":
            if args.limit < 1:
                raise ValueError("--limit must be at least 1")
            result = RebrickableClient().search_sets(args.query, args.limit)
        elif args.command == "send-message":
            result = TelegramBot().send_message(args.chat_id, args.text)
        elif args.command == "sync":
            count = sync_architecture()
            print(f"Stored {count} Architecture sets in SQLite.")
            return 0
        else:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s %(levelname)s %(message)s",
            )
            count = sync_architecture()
            print(f"Loaded {count} Architecture sets. Starting Telegram bot.")
            run_polling()
            return 0
    except (APIError, ConfigurationError, ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())