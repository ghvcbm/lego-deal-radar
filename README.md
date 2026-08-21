# Rebrickable Telegram Bot

A small, dependency-free Python project that reads LEGO set data from the
Rebrickable API and sends messages through the Telegram Bot API.

API credentials are read only from environment variables. They are never
stored in source code.

## Configuration

Set these variables in your Replit Secrets or shell environment:

```bash
export REBRICKABLE_API_KEY="your-rebrickable-key"
export TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
```

`REBRICKABLE_API_KEY` is needed for Rebrickable commands. `TELEGRAM_BOT_TOKEN`
is needed for Telegram commands.

On Replit, add both values as Secrets, then start the configured
`LEGO Deal Radar Bot` workflow. The workflow runs the bot from this directory
and keeps it listening for Telegram updates.

## Run it

From the project directory, with `src` on the Python path:

```bash
PYTHONPATH=src python -m python_project sync
PYTHONPATH=src python -m python_project bot
PYTHONPATH=src python -m python_project lookup-set <set-number>
PYTHONPATH=src python -m python_project search-sets "Architecture" --limit 5
PYTHONPATH=src python -m python_project send-message 123456789 "New set found!"
```

The `sync` command finds the exact Rebrickable theme named `Architecture`,
retrieves every page of sets in that theme, and replaces the local SQLite
catalog. The `bot` command performs that sync at startup and then listens for
Telegram updates.

If the package is installed in editable mode:

```bash
python -m pip install -e .
lego-deal-radar sync
lego-deal-radar bot
```

## Telegram commands

- `/start` — shows a welcome message and available command.
- `/architecture` — sends the stored Architecture set count and every set's
  number, name, year, and part count.

Messages are split into Telegram-safe chunks when the catalog is long.

## Current scope

This version intentionally does not include Vinted, Leboncoin, eBay, price
scoring, automated deal detection, or marketplace monitoring.

## Run tests

```bash
PYTHONPATH=src python -m unittest discover -s tests
```