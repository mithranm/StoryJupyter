# storyjupyter/core/protocols.py
from collections.abc import Sequence
from typing import Protocol, TypeVar, overload, Any
from typing_extensions import Literal
from datetime import datetime
from .types import TimeSpec, Duration, EventMetadata, OutputFormat
from .models import Character, Brand, TimelineEvent

T = TypeVar("T")

class BrandManager(Protocol):
    """Manages brand name consistency"""
    @overload
    def get_brand(self, real_name: str) -> Brand: ...
    
    @overload
    def get_brand(self, real_name: str, default: T) -> Brand | T: ...
    
    def batch_generate(self, names: Sequence[str]) -> Sequence[Brand]: ...
    def validate_name(self, name: str) -> tuple[bool, str]: ...

class TimelineManager(Protocol):
    """Manages story timeline and events"""
    def set_time(self, time: TimeSpec, /) -> None: ...
    def advance_time(self, duration: Duration, /) -> None: ...
    def add_event(
        self, 
        content: str, 
        *, 
        metadata: EventMetadata | None = None
    ) -> TimelineEvent: ...
    def get_events(
        self, 
        *, 
        start: TimeSpec | None = None,
        end: TimeSpec | None = None,
        tags: Sequence[str] | None = None
    ) -> Sequence[TimelineEvent]: ...

class StoryContext(Protocol):
    """Main interface for story management"""
    brands: BrandManager
    timeline: TimelineManager
    
    async def compile(
        self, 
        notebooks: Sequence[str], 
        *, 
        format: OutputFormat = "markdown"
    ) -> str: ...
    
    def export_reference(self) -> dict[str, Sequence[Brand]]: ...
    def get_analytics(self) -> dict[str, Any]: ...