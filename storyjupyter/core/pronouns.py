# storyjupyter/core/pronouns.py
from .types import PronounSet

class Pronouns:
    """Manages character pronouns and their variations"""
    
    # Mapping of pronoun sets to their forms
    _PRONOUN_FORMS = {
        "he": {
            "subject": "he",
            "object": "him",
            "possessive": "his",  # his book
            "possessive_pronoun": "his",  # the book is his
            "reflexive": "himself"
        },
        "she": {
            "subject": "she",
            "object": "her",
            "possessive": "her",  # her book
            "possessive_pronoun": "hers",  # the book is hers
            "reflexive": "herself"
        },
        "they": {
            "subject": "they",
            "object": "them",
            "possessive": "their",  # their book
            "possessive_pronoun": "theirs",  # the book is theirs
            "reflexive": "themselves"
        }
    }
    
    def __init__(self, pronoun_set: PronounSet) -> None:
        """Initialize pronouns with a specific set."""
        if pronoun_set not in self._PRONOUN_FORMS:
            raise ValueError(f"Invalid pronoun set: {pronoun_set}")
        self.pronoun_set = pronoun_set
        self._forms = self._PRONOUN_FORMS[pronoun_set]
    
    @property
    def subject(self) -> str:
        """Returns subject pronoun (he/she/they)"""
        return self._forms["subject"]
        
    @property
    def object(self) -> str:
        """Returns object pronoun (him/her/them)"""
        return self._forms["object"]
        
    @property
    def possessive(self) -> str:
        """Returns possessive adjective (his/her/their)"""
        return self._forms["possessive"]
        
    @property
    def possessive_pronoun(self) -> str:
        """Returns possessive pronoun (his/hers/theirs)"""
        return self._forms["possessive_pronoun"]
        
    @property
    def reflexive(self) -> str:
        """Returns reflexive pronoun (himself/herself/themselves)"""
        return self._forms["reflexive"]
    
    def __str__(self) -> str:
        """String representation showing subject/object/possessive"""
        return f"{self.subject}/{self.object}/{self.possessive}"