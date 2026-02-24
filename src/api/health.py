"""Health check system for monitoring service status."""

import time
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import select

from ..config import Config
from ..custom_logger import CustomLogger
from ..db.cache.utils import get_player_count, last_updated_at
from ..db.database import SQLAlchemySession

logger = CustomLogger("health")

# Track service start time
_start_time = time.time()


def check_database() -> Dict[str, Any]:
    """
    Check database connectivity by executing a simple query.

    Returns:
        dict with 'status' key: 'ok' or 'error'
    """
    try:
        db = SQLAlchemySession()
        # execute a harmless SQLAlchemy select to verify connectivity
        db.execute(select(1))
        db.close()
        return {"status": "ok"}
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return {"status": "error", "error": str(e)}


def check_cache() -> Dict[str, Any]:
    """
    Check leaderboard cache status and staleness.

    Returns:
        dict with status ('ok', 'degraded', 'warning', 'error') and cache metrics
    """
    try:
        player_count = get_player_count()
        last_updated = last_updated_at()

        if last_updated is None:
            return {"status": "warning", "message": "Cache has never been updated"}

        age_seconds = int(datetime.now(timezone.utc).timestamp()) - int(last_updated)
        cache_stale = age_seconds > (Config.cache_update_interval * 2)

        return {
            "status": "degraded" if cache_stale else "ok",
            "last_updated": datetime.fromtimestamp(last_updated, tz=timezone.utc).isoformat(),
            "player_count": player_count,
            "age_seconds": age_seconds,
            "update_interval": Config.cache_update_interval,
        }
    except Exception as e:
        logger.error("Cache health check failed", error=str(e))
        return {"status": "error", "error": str(e)}


def check_discord_bot() -> Dict[str, Any]:
    """
    Check Discord bot connectivity and login status.

    Returns:
        dict with status and bot information (username, user_id, guild count)
    """
    try:
        # Import here to avoid circular dependency at module load time
        from ..bot.bot import client

        if client.user is None:
            return {"status": "disconnected", "message": "Bot not logged in"}

        return {
            "status": "ok",
            "connected": True,
            "guilds": len(client.guilds),
        }
    except Exception as e:
        logger.error("Discord bot health check failed", error=str(e))
        return {"status": "error", "error": str(e)}


def determine_overall_status(checks: Dict[str, Dict[str, Any]]) -> str:
    """
    Determine overall service health from individual check results.

    Args:
        checks: Dictionary of check name -> check result

    Returns:
        'healthy', 'degraded', or 'unhealthy'
    """
    statuses = [check.get("status") for check in checks.values()]

    if any(s in ("error", "disconnected") for s in statuses):
        return "unhealthy"
    elif any(s in ("degraded", "warning") for s in statuses):
        return "degraded"
    else:
        return "healthy"


def get_health_status() -> Dict[str, Any]:
    """
    Perform all health checks and return comprehensive status.

    Returns:
        dict containing overall status, uptime, and individual check results
    """
    uptime_seconds = int(time.time() - _start_time)

    # Run individual checks
    checks = {
        "database": check_database(),
        "cache": check_cache(),
        "discord_bot": check_discord_bot(),
    }

    overall_status = determine_overall_status(checks)

    # Map internal statuses to RFC Health Check statuses: pass, warn, fail
    def _to_rfc_status(s: str) -> str:
        if s in ("ok", "healthy"):
            return "pass"
        if s in ("degraded", "warning", "warn"):
            return "warn"
        return "fail"

    now_iso = datetime.now(timezone.utc).isoformat()

    rfc_checks: Dict[str, Any] = {}
    for name, result in checks.items():
        status = result.get("status") if isinstance(result, dict) else None
        rfc_checks[name] = {
            "status": _to_rfc_status(status),
            "time": now_iso,
            "output": result,
        }

    rfc_overall = _to_rfc_status(overall_status)

    response = {
        "schemaVersion": 1,
        "name": "betterburn",
        "status": rfc_overall,
        "time": now_iso,
        "uptime_seconds": uptime_seconds,
        "checks": rfc_checks,
    }

    logger.debug("Health check completed", status=overall_status)
    return response
