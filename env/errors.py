"""Custom exception classes for the Dec-POMDP environment."""


class ConfigValidationError(Exception):
    """Raised when a config field is missing or has an invalid type.

    The message always contains the name of the offending field.
    """


class MessageDimensionError(Exception):
    """Raised when a message vector has the wrong length (expected 16)."""


class EpisodeTerminatedError(Exception):
    """Raised when step() is called on a terminated episode."""


class BoundaryViolationError(Exception):
    """Raised when an entity placement falls outside the grid bounds."""


class GenerationFailedError(Exception):
    """Raised when the procedural generator exhausts retries without finding a valid layout."""
