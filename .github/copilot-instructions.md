# Betterburn — Copilot Instructions

## Architecture Overview

Betterburn is a **rank verification bot** for Steam game app `2217000`. It links Discord accounts to Steam, fetches leaderboard ELO scores, maps scores to ranks (Stone→Aetherean), and assigns corresponding Discord roles.

**Two services run in one process** (`src/main.py`): a **discord.py Bot** on the main thread and a **FastAPI server** on a background thread. They communicate through `src/bridge.py`, an in-memory session store that bridges the Steam OpenID callback (FastAPI) back to the Discord interaction that initiated it.

### Data Flow: Account Linking
1. User runs `/link` → bot creates a DB session + in-memory `LinkedSession` with an event handler
2. Bot sends a button linking to `FastAPI /api/link?sessionId=...`
3. FastAPI redirects to Steam OpenID, then handles callback at `/api/auth`
4. `/api/auth` validates, calls `bridge.find_linked_session()`, fires the event handler back on the bot's event loop
5. Bot edits the original Discord message to confirm the link

### Database Layout (`src/db/`)
Three sub-packages, each with `models.py` (SQLAlchemy models) and `utils.py` (query functions):
- **`cache/`** — `LeaderboardRow` + `Metadata`: periodically refreshed Steam leaderboard snapshot
- **`discord/`** — `UserTable`, `RoleTable`, `MembershipTable`: Discord↔Steam links and guild role mappings
- **`session/`** — `Session`: temporary auth sessions with expiry

All DB access uses `SQLAlchemySession()` from `src/db/database.py` (SQLite, file: `betterburn.db`). Sessions are manually opened/closed — there is no context manager pattern; always call `db.close()` in a `finally` block.

### Bot Structure (`src/bot/`)
- Slash commands are defined directly in `bot.py` and scoped to `Config.test_guild` IDs
- **Cogs**: `MaidCog` (background tasks: cache refresh, session culling) and `RoleCog` (role assignment, `/config`, `/roledoctor`)
- **Views**: `LinkView` and `UnlinkView` in `src/bot/views/__init__.py`

## Development

- **Python env**: `.venv` virtualenv, dependencies in `pyproject.toml`
- **Linter**: `ruff` with 120-char line length, auto-fix enabled
- **Tests**: `pytest` + `pytest-asyncio` — run with `pytest` from project root. Tests use `monkeypatch` to stub `SQLAlchemySession` with dummy objects (see `tests/test_discord_utils.py` for the pattern)
- **Config**: `config.toml` at project root, loaded at import-time by `src/config.py` into the `Config` class (static attributes)

## Conventions

- **Logging**: Use `CustomLogger` from `src/custom_logger.py` (structlog-based). Import the default `logger` for infrastructure/top-level code (`from .custom_logger import logger`) or create component-specific loggers (`logger = CustomLogger("component_name")`). Never use stdlib `logging` directly. Examples:
  - `main.py`, `bridge.py` → use default `logger` (root logger)
  - `bot.py` → `CustomLogger("discord")`
  - `api.py` → `CustomLogger("fastapi")`
  - Cogs/modules → create their own (e.g., `CustomLogger("maid")`)
- **Rank thresholds** are defined in `src/db/cache/utils.py::get_rank_from_row()` — score ranges map to `Rank` enum values from `src/constants.py`
- **Signals**: `src/signals/__init__.py` provides `onUserLinked` and `onUserUnlinked` — async signals emitted from `src/db/discord/utils.py` on link/unlink
- **Imports**: Use relative imports within `src/` (e.g., `from ..config import Config`)
- **Slash commands** are guild-scoped via `Config.test_guild`; synced in `on_ready`