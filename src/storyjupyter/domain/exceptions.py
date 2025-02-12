class StoryError(Exception):
    """Base class for story-related errors"""

    pass


class UninitializedStoryError(StoryError):
    """Raised when trying to use story features before proper initialization"""

    pass


class UninitializedLocationError(StoryError):
    """Raised when trying to add events without setting a location"""

    pass


class InvalidTimelineError(StoryError):
    """Raised when timeline consistency is violated"""

    pass
