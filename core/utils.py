"""Utility umum CTW."""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Wrapper timezone-aware utcnow. Menggantikan datetime.utcnow() yang deprecated."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
