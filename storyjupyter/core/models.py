# storyjupyter/core/models.py
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any, Optional, Dict
from .types import EventMetadata, PronounSet
from .pronouns import Pronouns
@dataclass
class NameComponents:
    """Flexible name structure allowing any combination of components"""
    first: Optional[str] = None
    middle: list[str] = field(default_factory=list)  # Any number of middle names
    last: Optional[str] = None
    prefix: Optional[str] = None  # For titles, honorifics, etc.
    suffix: Optional[str] = None  # For generational suffixes, credentials, etc.
    
    def __str__(self) -> str:
        """Intelligent string representation based on available components"""
        components = []
        if self.prefix:
            components.append(self.prefix)
        if self.first:
            components.append(self.first)
        if self.middle:
            components.append(" ".join(self.middle))
        if self.last:
            components.append(self.last)
        if self.suffix:
            components.append(self.suffix)
        return " ".join(components)

@dataclass
class Character:
    """
    Flexible character representation that can accommodate any combination of attributes.
    All fields are optional to allow maximum flexibility in character creation.
    """
    character_id: str
    name_components: NameComponents
    pronouns: Optional[Pronouns] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    relationships: Dict[str, Any] = field(default_factory=dict)
    chapter_introduced: Optional[int] = None
    
    @property
    def name(self) -> str:
        """Name Component Object Of Character"""
        return self.name_components
    
    def __str__(self) -> str:
        """String representation showing all attributes"""
        return str({
            "character_id": self.character_id,
            "name_components": str(self.name_components),
            "pronouns": str(self.pronouns) if self.pronouns else None,
            "attributes": self.attributes,
            "relationships": self.relationships
        })
    
    @classmethod
    def create(
        cls,
        *,
        first_name: Optional[str] = None,
        middle_names: Optional[list[str]] = None,
        last_name: Optional[str] = None,
        prefix: Optional[str] = None,
        suffix: Optional[str] = None,
        pronoun_set: Optional[str] = None,
        **attributes
    ) -> "Character":
        """
        Factory method supporting flexible character creation.
        All parameters are optional to allow any combination of attributes.
        """
        # Extract relationship attributes
        relationships = {k[12:]: v for k, v in attributes.items() 
                       if k.startswith("relationship_")}
        for k in relationships.keys():
            attributes.pop(f"relationship_{k}")
            
        return cls(
            name_components=NameComponents(
                first=first_name,
                middle=middle_names or [],
                last=last_name,
                prefix=prefix,
                suffix=suffix
            ),
            pronouns=Pronouns(pronoun_set) if pronoun_set else None,
            attributes=attributes,
            relationships=relationships
        )
    
    def update(
        self,
        *,  # Force keyword arguments
        first_name: Optional[str] = None,
        middle_names: Optional[list[str]] = None,
        last_name: Optional[str] = None,
        prefix: Optional[str] = None,
        suffix: Optional[str] = None,
        pronoun_set: Optional[str] = None,
        **attributes
    ) -> "Character":
        """Create a new Character instance with updated attributes"""
        # Start with current name components
        new_components = NameComponents(
            first=first_name if first_name is not None else self.name_components.first,
            middle=middle_names if middle_names is not None else self.name_components.middle.copy(),
            last=last_name if last_name is not None else self.name_components.last,
            prefix=prefix if prefix is not None else self.name_components.prefix,
            suffix=suffix if suffix is not None else self.name_components.suffix
        )
        
        # Update pronouns if specified
        new_pronouns = Pronouns(pronoun_set) if pronoun_set else self.pronouns
        
        # Extract and update relationships
        new_relationships = self.relationships.copy()
        relationship_updates = {k[12:]: v for k, v in attributes.items() 
                              if k.startswith("relationship_")}
        new_relationships.update(relationship_updates)
        
        # Update regular attributes
        new_attributes = self.attributes.copy()
        regular_updates = {k: v for k, v in attributes.items() 
                         if not k.startswith("relationship_")}
        new_attributes.update(regular_updates)
        
        return Character(
            name_components=new_components,
            pronouns=new_pronouns,
            attributes=new_attributes,
            relationships=new_relationships
        )

@dataclass(frozen=True, slots=True)
class Brand:
    """Immutable brand representation"""
    real_name: str
    story_name: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any, Optional, Dict
from .types import EventMetadata, PronounSet
from .pronouns import Pronouns

@dataclass(frozen=True, slots=True)
class TimelineEvent:
    """Immutable timeline event"""
    timestamp: datetime
    location: str
    content: str
    chapter: int
    event_id: str
    metadata: EventMetadata = field(default_factory=lambda: {"tags": []})


    def __post_init__(self) -> None:
        if not isinstance(self.timestamp, datetime):
            object.__setattr__(self, "timestamp", datetime.fromisoformat(str(self.timestamp)))
        if self.timestamp.tzinfo is None:
            object.__setattr__(self, "timestamp", self.timestamp.replace(tzinfo=UTC))