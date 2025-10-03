"""
IST (Indian Standard Time) timezone utilities for SafeHorizon Backend

This module provides utilities to ensure all timestamps in the application
use IST timezone consistently.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

# IST is UTC+5:30
IST = timezone(timedelta(hours=5, minutes=30))


def now_ist() -> datetime:
    """Get current datetime in IST timezone"""
    return datetime.now(IST)


def utc_to_ist(utc_dt: datetime) -> datetime:
    """Convert UTC datetime to IST"""
    if utc_dt.tzinfo is None:
        # If no timezone info, assume UTC
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(IST)


def ist_to_utc(ist_dt: datetime) -> datetime:
    """Convert IST datetime to UTC"""
    if ist_dt.tzinfo is None:
        # If no timezone info, assume IST
        ist_dt = ist_dt.replace(tzinfo=IST)
    return ist_dt.astimezone(timezone.utc)


def ensure_ist(dt: Optional[datetime] = None) -> datetime:
    """
    Ensure datetime is in IST timezone.
    If dt is None, returns current IST time.
    If dt has no timezone, assumes it's in IST.
    If dt has timezone, converts to IST.
    """
    if dt is None:
        return now_ist()
    
    if dt.tzinfo is None:
        # No timezone info, assume IST
        return dt.replace(tzinfo=IST)
    
    # Has timezone info, convert to IST
    return dt.astimezone(IST)


def ist_isoformat(dt: Optional[datetime] = None) -> str:
    """Get ISO format string for IST datetime"""
    return ensure_ist(dt).isoformat()


def parse_to_ist(date_string: str) -> datetime:
    """Parse ISO date string and convert to IST"""
    dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    return ensure_ist(dt)