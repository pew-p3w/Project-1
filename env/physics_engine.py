"""Physics engine: pymunk wrapper for the Dec-POMDP environment."""

from __future__ import annotations

import pymunk

from env.config_loader import EnvConfig
from env.objects import CircleDef, PolygonDef, RectDef


class PhysicsEngine:
    """Wraps a pymunk.Space providing the physics simulation for the environment.

    Responsibilities:
    - Maintain four static boundary walls enclosing the world.
    - Manage Agent B's dynamic circular body.
    - Manage static obstacle bodies/shapes.
    - Advance the simulation and expose position/velocity queries.
    """

    def __init__(self, config: EnvConfig) -> None:
        """Create pymunk Space; add four static segment shapes for world boundary walls."""
        self._config = config
        self._space = pymunk.Space()
        self._space.gravity = (0.0, 0.0)

        # Agent B body and shape (set when add_agent_b is called)
        self._agent_b_body: pymunk.Body | None = None
        self._agent_b_shape: pymunk.Circle | None = None

        # Track obstacle bodies so we can remove them on reset
        self._obstacle_bodies: list[pymunk.Body] = []
        self._obstacle_shapes: list[pymunk.Shape] = []

        # Boundary wall segments (static)
        self._boundary_shapes: list[pymunk.Segment] = []
        self._add_boundary_walls()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _add_boundary_walls(self) -> None:
        """Create four static segment shapes along the world edges."""
        w = self._config.world_width
        h = self._config.world_height
        static_body = self._space.static_body

        walls = [
            # bottom
            pymunk.Segment(static_body, (0.0, 0.0), (w, 0.0), 0),
            # top
            pymunk.Segment(static_body, (0.0, h), (w, h), 0),
            # left
            pymunk.Segment(static_body, (0.0, 0.0), (0.0, h), 0),
            # right
            pymunk.Segment(static_body, (w, 0.0), (w, h), 0),
        ]
        for seg in walls:
            seg.elasticity = 0.5
            seg.friction = 0.0
        self._space.add(*walls)
        self._boundary_shapes = walls

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_agent_b(self, x: float, y: float, agent_radius: float) -> None:
        """Create dynamic circular body for Agent B at (x, y)."""
        mass = 1.0
        moment = pymunk.moment_for_circle(mass, 0, agent_radius)
        body = pymunk.Body(mass, moment)
        body.position = (x, y)
        shape = pymunk.Circle(body, agent_radius)
        shape.elasticity = 0.5
        shape.friction = 0.0
        self._space.add(body, shape)
        self._agent_b_body = body
        self._agent_b_shape = shape

    def add_obstacle(self, shape_def: RectDef | CircleDef | PolygonDef) -> None:
        """Create static shape for an obstacle and add to space."""
        body = pymunk.Body(body_type=pymunk.Body.STATIC)

        if isinstance(shape_def, RectDef):
            body.position = (shape_def.cx, shape_def.cy)
            body.angle = shape_def.angle
            shape: pymunk.Shape = pymunk.Poly.create_box(
                body, (shape_def.width, shape_def.height)
            )
        elif isinstance(shape_def, CircleDef):
            body.position = (shape_def.cx, shape_def.cy)
            shape = pymunk.Circle(body, shape_def.radius)
        elif isinstance(shape_def, PolygonDef):
            body.position = (0.0, 0.0)
            shape = pymunk.Poly(body, shape_def.vertices)
        else:
            raise TypeError(f"Unknown shape_def type: {type(shape_def)}")

        shape.elasticity = 0.8
        shape.friction = 0.0
        self._space.add(body, shape)
        self._obstacle_bodies.append(body)
        self._obstacle_shapes.append(shape)

    def set_velocity(self, vx: float, vy: float) -> None:
        """Set Agent B's body velocity."""
        if self._agent_b_body is None:
            raise RuntimeError("Agent B has not been added to the physics engine.")
        self._agent_b_body.velocity = (vx, vy)

    # Number of substeps used per logical step to prevent tunneling at high velocities.
    # With max_speed=200 and dt=1.0, each substep moves 200/1000=0.2 units,
    # well within the agent_radius (typically 10), preventing tunneling.
    _SUBSTEPS: int = 1000

    def step(self, dt: float = 1.0) -> None:
        """Advance pymunk space by dt. Resolves all collisions.

        Uses internal substeps to prevent tunneling at high velocities.
        """
        sub_dt = dt / self._SUBSTEPS
        for _ in range(self._SUBSTEPS):
            self._space.step(sub_dt)

    def get_agent_b_position(self) -> tuple[float, float]:
        """Query Agent B's position from pymunk after integration."""
        if self._agent_b_body is None:
            raise RuntimeError("Agent B has not been added to the physics engine.")
        pos = self._agent_b_body.position
        return (float(pos.x), float(pos.y))

    def get_agent_b_velocity(self) -> tuple[float, float]:
        """Query Agent B's actual velocity after collision response."""
        if self._agent_b_body is None:
            raise RuntimeError("Agent B has not been added to the physics engine.")
        vel = self._agent_b_body.velocity
        return (float(vel.x), float(vel.y))

    def reset(self) -> None:
        """Remove all bodies and shapes; recreate boundary segments."""
        # Remove Agent B
        if self._agent_b_body is not None:
            self._space.remove(self._agent_b_body, self._agent_b_shape)
            self._agent_b_body = None
            self._agent_b_shape = None

        # Remove obstacles
        for body, shape in zip(self._obstacle_bodies, self._obstacle_shapes):
            self._space.remove(shape, body)
        self._obstacle_bodies.clear()
        self._obstacle_shapes.clear()

        # Remove old boundary wall shapes (attached to static_body)
        for seg in self._boundary_shapes:
            self._space.remove(seg)
        self._boundary_shapes.clear()

        # Recreate boundary walls
        self._add_boundary_walls()
