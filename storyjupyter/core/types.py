# storyjupyter/core/types.py
from datetime import datetime, timedelta
from typing import TypeAlias
from typing_extensions import TypedDict, Literal

# Basic type aliases
TimeSpec: TypeAlias = datetime | str
Duration: TypeAlias = timedelta | str
LocationId: TypeAlias = str
CharacterId: TypeAlias = str
OutputFormat = Literal["markdown", "html", "pdf"]
PronounSet = Literal["he", "she", "they"]

# Type definitions
class EventMetadata(TypedDict, total=False):
    character_ids: list[CharacterId]
    location_ids: list[LocationId]
    tags: list[str]
    importance: Literal["low", "medium", "high"]