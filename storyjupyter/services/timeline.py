# storyjupyter/services/timeline.py
from datetime import datetime, UTC, timedelta
import re
from typing import Sequence, Optional
from ..core.types import TimeSpec, Duration, EventMetadata
from ..core.models import TimelineEvent
from ..core.protocols import TimelineManager
from ..persistence.repositories import TimelineRepository
class ParseError(Exception):
    """Error raised when parsing time or duration fails"""
    pass

class StoryTimelineManager(TimelineManager):
    """Manages story timeline and events"""
    
    _DURATION_PATTERNS = {
        # Basic patterns with explicit unit markers
        r"(\d+)\s*min(?:ute)?s?$": lambda x: timedelta(minutes=int(x)),
        r"(\d+)\s*hour?s?$": lambda x: timedelta(hours=int(x)),
        r"(\d+)\s*day?s?$": lambda x: timedelta(days=int(x)),
        r"(\d+)\s*week?s?$": lambda x: timedelta(weeks=int(x)),
        
        # Combined patterns (must come after basic patterns)
        r"(\d+)\s*hour?s?\s*(\d+)\s*min(?:ute)?s?$": 
            lambda h, m: timedelta(hours=int(h), minutes=int(m)),
        r"(\d+):(\d+)(?::(\d+))?$": 
            lambda h, m, s=0: timedelta(hours=int(h), minutes=int(m), seconds=int(s or 0))
    }
    
    def __init__(self, repository :TimelineRepository):
        self.repository = repository 
        self._current_time: Optional[datetime] = None
        self._current_location: Optional[str] = None
    
    def _parse_time(self, time: TimeSpec) -> datetime:
        """Parse TimeSpec into datetime with UTC timezone"""
        try:
            if isinstance(time, str):
                dt = datetime.fromisoformat(time)
                return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
            return time if time.tzinfo else time.replace(tzinfo=UTC)
        except (ValueError, TypeError) as e:
            raise ParseError(f"Invalid time format: {time}") from e
    
    def _parse_duration(self, duration: Duration) -> timedelta:
        """Parse duration string or timedelta"""
        if isinstance(duration, timedelta):
            return duration
            
        if not isinstance(duration, str):
            raise ParseError(f"Duration must be string or timedelta, got {type(duration)}")
        
        # Normalize input string
        duration_str = duration.lower().strip()
        
        # Try each pattern
        for pattern, converter in self._DURATION_PATTERNS.items():
            if match := re.match(pattern, duration_str):
                try:
                    return converter(*match.groups())
                except (ValueError, TypeError) as e:
                    raise ParseError(f"Invalid duration format: {duration}") from e
        
        raise ParseError(f"Unrecognized duration format: {duration}")
    
    def set_time(self, time: datetime) -> None:
        """Set current story time"""
        self._current_time = time
      
    def clear_chapter(self, chapter: int) -> None:
        """Clear all events for a specific chapter"""
        self.repository.delete_events(chapter=chapter)
    
    def advance_time(self, duration: str) -> None:
        """Advance story time by duration"""
        if not self._current_time:
            raise RuntimeError("Current time not set. Call set_time() first.")
        duration_delta = self._parse_duration(duration)
        self._current_time += duration_delta
    
    def get_current_time(self) -> datetime:
        """Get current story time"""
        if not self._current_time:
            raise RuntimeError("Current time not set. Call set_time() first.")
        return self._current_time
    
    def set_location(self, location: str) -> None:
        """Set current story location"""
        self._current_location = location
        
    def get_current_location(self) -> str:
        """Get current story location"""
        return self._current_location or "Unspecified Location"
    
    def add_event(
        self,
        content: str,
        chapter: int,
        event_id: str,
        *,
        metadata: Optional[EventMetadata] = None,
    ) -> TimelineEvent:
        """Add event to timeline at current time and location"""
        if not self._current_time:
            raise RuntimeError("Current time not set. Call set_time() first.")

        event = TimelineEvent(
            event_id=event_id,
            timestamp=self._current_time,
            location=self.get_current_location(),
            content=content,
            metadata=metadata or {"tags": []},
            chapter=chapter,
        )
        self.repository.save_timeline_event(event)
        return event
    
    def get_events(self, chapter: Optional[int] = None) -> Sequence[TimelineEvent]:
        return self.repository.get_all_timeline_events(chapter=chapter)

    def clear_chapter(self, chapter: int):
        self.repository.delete_events(chapter)
        
    def clear_from_chapter_onwards(self, chapter: int) -> None:
        """Clear all events from the specified chapter onwards."""
        # Fetch all events from the specified chapter onwards
        for event in self.repository.get_all_timeline_events():
            if event.chapter >= chapter:
                self.repository.delete_timeline_event(event.event_id)