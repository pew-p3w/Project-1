"""Abstract base entity for the Dec-POMDP environment."""

from dataclasses import dataclass


@dataclass
class Entity:
    """Base class for all world objects.

    Attributes:
        id: Unique identifier for this entity.
        x: Grid x-coordinate.
        y: Grid y-coordinate.
        static: Whether the entity never moves.
        collidable: Whether other entities are blocked from occupying this position.
    """

    id: str
    x: int
    y: int
    static: bool
    collidable: bool
