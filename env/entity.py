"""Base Entity dataclass for the Dec-POMDP environment."""

from dataclasses import dataclass


@dataclass
class Entity:
    """Base entity with a unique id, float position, and static/collidable flags.

    __eq__ and __hash__ are based on id only, so entities remain hashable
    after position updates.
    """

    id: str
    x: float
    y: float
    static: bool
    collidable: bool

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
