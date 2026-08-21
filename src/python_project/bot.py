"""Telegram polling loop for LEGO Deal Radar."""

from __future__ import annotations

import logging
import time

from .database import connect, list_architecture_sets
from .telegram import TelegramBot, format_architecture_sets

LOGGER = logging.getLogger(__name__)


def handle_update(bot: TelegramBot, update: dict, db_path: str | None = None) -> None:
    """Handle supported Telegram commands from one update."""
    message = update.get("message")
    if not isinstance(message, dict):
        return
    text = message.get("text")
    chat = message.get("chat")
    if not isinstance(text, str) or not isinstance(chat, dict):
        return
    chat_id = chat.get("id")
    if chat_id is None:
        return

    command = text.strip().split(maxsplit=1)[0].split("@", maxsplit=1)[0].lower()
    if command == "/start":
        bot.send_message(
            str(chat_id),
            "Welcome to LEGO Deal Radar.\n"
            "Use /architecture to view the current Rebrickable Architecture catalog.",
        )
    elif command == "/architecture":
        connection = connect(db_path)
        try:
            messages = format_architecture_sets(list_architecture_sets(connection))
        finally:
            connection.close()
        for response in messages:
            bot.send_message(str(chat_id), response)


def run_polling(db_path: str | None = None, poll_timeout: int = 25) -> None:
    """Run the bot until interrupted."""
    bot = TelegramBot()
    offset: int | None = None
    LOGGER.info("LEGO Deal Radar is listening for Telegram commands")
    while True:
        try:
            updates = bot.get_updates(offset=offset, timeout=poll_timeout)
            for update in updates:
                update_id = update.get("update_id")
                if isinstance(update_id, int):
                    offset = update_id + 1
                try:
                    handle_update(bot, update, db_path)
                except Exception:
                    LOGGER.exception("Failed to handle a Telegram update")
        except KeyboardInterrupt:
            LOGGER.info("Bot stopped")
            return
        except Exception:
            LOGGER.exception("Telegram polling failed; retrying shortly")
            time.sleep(5)