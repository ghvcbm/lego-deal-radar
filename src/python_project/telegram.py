"""Client for the Telegram Bot API."""

from __future__ import annotations

from urllib.parse import quote, urlencode

from .config import required_env
from .database import ArchitectureSet
from .http import APIError, request_json


class TelegramBot:
    """Send messages through a Telegram bot."""

    base_url = "https://api.telegram.org"

    def __init__(self, token: str | None = None) -> None:
        self.token = token or required_env("TELEGRAM_BOT_TOKEN")

    def send_message(self, chat_id: str, text: str) -> dict:
        """Send a text message to a Telegram chat."""
        response = self._call(
            "sendMessage",
            body={"chat_id": chat_id, "text": text},
        )
        return response

    def get_updates(self, offset: int | None = None, timeout: int = 25) -> list[dict]:
        """Long-poll Telegram for incoming messages."""
        query = {"timeout": timeout, "allowed_updates": '["message"]'}
        if offset is not None:
            query["offset"] = offset
        response = self._call("getUpdates", query=query)
        result = response.get("result")
        if not isinstance(result, list):
            raise APIError("Telegram returned an invalid updates response.")
        return [item for item in result if isinstance(item, dict)]

    def _call(
        self,
        method: str,
        *,
        query: dict[str, object] | None = None,
        body: dict[str, object] | None = None,
    ) -> dict:
        url = f"{self.base_url}/bot{quote(self.token, safe='')}/{method}"
        if query:
            url = f"{url}?{urlencode(query)}"
        response = request_json(
            url,
            method="POST" if body is not None else "GET",
            body=body,
        )
        if response.get("ok") is not True:
            raise RuntimeError(f"Telegram API request was not successful: {response}")
        return response


def format_architecture_sets(sets: list[ArchitectureSet]) -> list[str]:
    """Format the catalog into Telegram-sized messages."""
    if not sets:
        return ["Architecture catalog is empty. Run the sync command first."]

    lines = [f"LEGO Architecture: {len(sets)} sets"]
    lines.extend(
        f"{item.set_num} — {item.name} ({item.year}, {item.num_parts} parts)"
        for item in sets
    )

    messages: list[str] = []
    current = ""
    for line in lines:
        candidate = f"{current}\n{line}".strip()
        if current and len(candidate) > 3900:
            messages.append(current)
            current = line
        else:
            current = candidate
    if current:
        messages.append(current)
    return messages