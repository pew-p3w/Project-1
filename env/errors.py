"""Custom exception hierarchy for the Dec-POMDP environment."""


class DecPOMDPError(Exception):
    """Base exception for all Dec-POMDP environment errors."""


class ConfigValidationError(DecPOMDPError):
    """Raised when a config field is missing or has an invalid type.

    The message always contains the name of the offending field.
    """


class MessageDimensionError(DecPOMDPError):
    """Raised when message_a length != 16.

    The message states the actual length received.
    """


class EpisodeTerminatedError(DecPOMDPError):
    """Raised when step() is called on a terminated episode."""


class GenerationFailedError(DecPOMDPError):
    """Raised when procedural generation cannot satisfy constraints within
    the retry budget. Message includes seed and config details.
    """


class InvalidObstacleError(ConfigValidationError):
    """Raised when an obstacle definition is invalid (e.g. zero-area
    rectangle, negative radius, fewer than 3 polygon vertices).

    Subclass of ConfigValidationError.
    """
