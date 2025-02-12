# src/storyjupyter/domain/time.py
from datetime import datetime, timezone, timedelta
from typing import Union, Optional
import re


class StoryTime:
    """Central time management for story elements"""

    # UTC timezone singleton
    UTC = timezone.utc

    @classmethod
    def now(cls) -> datetime:
        """Get current time in UTC"""
        return datetime.now(cls.UTC)

    @classmethod
    def ensure_tz(cls, dt: datetime) -> datetime:
        """Ensure datetime has UTC timezone"""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=cls.UTC)
        return dt

    @classmethod
    def parse_duration(cls, duration: Union[str, timedelta]) -> timedelta:
        """Parse duration string into timedelta"""
        if isinstance(duration, timedelta):
            return duration

        # Common duration patterns
        patterns = {
            r"(\d+)\s*min(?:ute)?s?": lambda x: timedelta(minutes=int(x)),
            r"(\d+)\s*hour?s?": lambda x: timedelta(hours=int(x)),
            r"(\d+)\s*day?s?": lambda x: timedelta(days=int(x)),
            r"(\d+)\s*week?s?": lambda x: timedelta(weeks=int(x)),
            r"(\d+):(\d+)(?::(\d+))?": lambda h, m, s=0: timedelta(
                hours=int(h), minutes=int(m), seconds=int(s or 0)
            ),
        }

        duration = duration.lower().strip()
        for pattern, converter in patterns.items():
            if match := re.match(pattern, duration):
                return converter(*match.groups())

        raise ValueError(f"Invalid duration format: {duration}")

    @classmethod
    def format_time(cls, dt: datetime, fmt: Optional[str] = None) -> str:
        """Format datetime for story display"""
        dt = cls.ensure_tz(dt)
        if fmt is None:
            return dt.strftime("%I:%M %p")  # Default to "3:30 PM" format
        return dt.strftime(fmt)
