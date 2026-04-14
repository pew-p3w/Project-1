"""Concrete entity types and shape definition dataclasses for the Dec-POMDP environment."""

from __future__ import annotations

from dataclasses import dataclass, field

from env.entity import Entity


# ---------------------------------------------------------------------------
# Shape definition dataclasses
# ---------------------------------------------------------------------------

@dataclass
class RectDef:
    cx: float
    cy: float
    width: float
    height: float
    angle: float  # radians


@dataclass
class CircleDef:
    cx: float
    cy: float
    radius: float


@dataclass
class PolygonDef:
    vertices: list[tuple[float, float]]  # ordered, convex, at least 3 points


# ---------------------------------------------------------------------------
# Concrete entity types
# ---------------------------------------------------------------------------

@dataclass(eq=False)
class AgentA(Entity):
    """Stationary observer agent. static=True, collidable=False."""

    def __init__(self, id: str, x: float, y: float) -> None:
        super().__init__(id=id, x=x, y=y, static=True, collidable=False)


@dataclass(eq=False)
class AgentB(Entity):
    """Dynamic actor agent. static=False, collidable=True.

    Extends Entity with heading/speed state and derived velocity components.
    """

    heading: float = 0.0  # radians, from positive x-axis
    speed: float = 0.0    # current scalar speed
    vx: float = 0.0       # derived: speed * cos(heading)
    vy: float = 0.0       # derived: speed * sin(heading)

    def __init__(
        self,
        id: str,
        x: float,
        y: float,
        heading: float = 0.0,
        speed: float = 0.0,
        vx: float = 0.0,
        vy: float = 0.0,
    ) -> None:
        super().__init__(id=id, x=x, y=y, static=False, collidable=True)
        self.heading = heading
        self.speed = speed
        self.vx = vx
        self.vy = vy


@dataclass(eq=False)
class Obstacle(Entity):
    """Static collidable obstacle. static=True, collidable=True.

    Extends Entity with a shape_def describing its geometry.
    """

    shape_def: RectDef | CircleDef | PolygonDef | None = None

    def __init__(
        self,
        id: str,
        x: float,
        y: float,
        shape_def: RectDef | CircleDef | PolygonDef | None = None,
    ) -> None:
        super().__init__(id=id, x=x, y=y, static=True, collidable=True)
        self.shape_def = shape_def


@dataclass(eq=False)
class Target(Entity):
    """Static non-collidable target. static=True, collidable=False.

    Capture is detected by Euclidean distance, not collision.
    """

    def __init__(self, id: str, x: float, y: float) -> None:
        super().__init__(id=id, x=x, y=y, static=True, collidable=False)
