"""Configuration loaded from environment variables."""

from __future__ import annotations

import os


class ConfigurationError(RuntimeError):
    """Raised when required environment configuration is missing."""


def required_env(name: str) -> str:
    """Return a required environment variable or raise a useful error."""
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigurationError(
            f"Missing {name}. Set it in the environment before running this command."
        )
    return value