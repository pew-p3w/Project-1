"""Concrete entity types for the Dec-POMDP environment."""

from dataclasses import dataclass

from env.entity import Entity


@dataclass(eq=False)
class AgentA(Entity):
    """Observer agent — full state visibility, no movement, non-collidable."""

    def __init__(self, id: str, x: int, y: int) -> None:
        super().__init__(id=id, x=x, y=y, static=False, collidable=False)


@dataclass(eq=False)
class AgentB(Entity):
    """Actor agent — blind, 8-directional movement, collidable."""

    def __init__(self, id: str, x: int, y: int) -> None:
        super().__init__(id=id, x=x, y=y, static=False, collidable=True)


@dataclass(eq=False)
class Obstacle(Entity):
    """Static collidable entity that blocks AgentB movement."""

    def __init__(self, id: str, x: int, y: int) -> None:
        super().__init__(id=id, x=x, y=y, static=True, collidable=True)


@dataclass(eq=False)
class Target(Entity):
    """Static non-collidable goal entity — AgentB may occupy its position."""

    def __init__(self, id: str, x: int, y: int) -> None:
        super().__init__(id=id, x=x, y=y, static=True, collidable=False)
