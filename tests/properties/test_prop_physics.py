"""Property-based tests for the PhysicsEngine.

Property 6: Physics Engine Prevents Penetration
Property 7: Boundary Containment

Feature: dec-pomdp-environment
"""

import math

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from env.config_loader import EnvConfig
from env.objects import CircleDef, PolygonDef, RectDef
from env.physics_engine import PhysicsEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cfg(world_width: float = 400.0, world_height: float = 300.0) -> EnvConfig:
    return EnvConfig(
        world_width=world_width,
        world_height=world_height,
        agent_radius=10.0,
        max_speed=200.0,
        max_angular_velocity=0.3,
        capture_radius=15.0,
        random_seed=0,
        max_steps=100,
        tau=1,
    )


# ---------------------------------------------------------------------------
# Property 6: Physics Engine Prevents Penetration
# ---------------------------------------------------------------------------

# Feature: dec-pomdp-environment, Property 6: Physics Engine Prevents Penetration
@settings(max_examples=100)
@given(
    start_x=st.floats(min_value=50.0, max_value=350.0),
    start_y=st.floats(min_value=50.0, max_value=250.0),
    vx=st.floats(min_value=-200.0, max_value=200.0),
    vy=st.floats(min_value=-200.0, max_value=200.0),
    n_steps=st.integers(min_value=1, max_value=20),
)
def test_prop_physics_no_penetration_boundary(
    start_x: float,
    start_y: float,
    vx: float,
    vy: float,
    n_steps: int,
) -> None:
    """Property 6: Physics Engine Prevents Penetration (boundary case).

    Agent B's circular body shall never overlap a world boundary by more
    than a negligible numerical tolerance (≤ 0.1 world units).
    Velocity is set once; pymunk preserves it between substeps.

    Validates: Requirements 4.5, 5.5
    """
    cfg = _make_cfg()
    engine = PhysicsEngine(cfg)
    engine.add_agent_b(start_x, start_y, cfg.agent_radius)
    # Set velocity once — pymunk preserves it between steps (no re-injection)
    engine.set_velocity(vx, vy)

    # Tolerance: pymunk resolves collisions with ~0.1 unit precision
    tolerance = 0.1
    for _ in range(n_steps):
        engine.step(dt=1.0)
        x, y = engine.get_agent_b_position()
        # Agent B's centre must be at least agent_radius - tolerance from each wall
        assert x >= cfg.agent_radius - tolerance, (
            f"Agent B penetrated left wall: x={x:.4f}, agent_radius={cfg.agent_radius}"
        )
        assert x <= cfg.world_width - cfg.agent_radius + tolerance, (
            f"Agent B penetrated right wall: x={x:.4f}"
        )
        assert y >= cfg.agent_radius - tolerance, (
            f"Agent B penetrated bottom wall: y={y:.4f}, agent_radius={cfg.agent_radius}"
        )
        assert y <= cfg.world_height - cfg.agent_radius + tolerance, (
            f"Agent B penetrated top wall: y={y:.4f}"
        )


# Feature: dec-pomdp-environment, Property 6: Physics Engine Prevents Penetration (obstacle)
@settings(max_examples=100)
@given(
    obs_cx=st.floats(min_value=100.0, max_value=300.0),
    obs_cy=st.floats(min_value=80.0, max_value=220.0),
    obs_radius=st.floats(min_value=10.0, max_value=30.0),
    vx=st.floats(min_value=-200.0, max_value=200.0),
    vy=st.floats(min_value=-200.0, max_value=200.0),
    n_steps=st.integers(min_value=1, max_value=20),
)
def test_prop_physics_no_penetration_circle_obstacle(
    obs_cx: float,
    obs_cy: float,
    obs_radius: float,
    vx: float,
    vy: float,
    n_steps: int,
) -> None:
    """Property 6: Physics Engine Prevents Penetration (circle obstacle).

    Agent B's circular body shall never overlap a circular obstacle by more
    than a negligible numerical tolerance (≤ 0.5 world units).

    Validates: Requirements 4.5, 5.5
    """
    cfg = _make_cfg()
    engine = PhysicsEngine(cfg)

    # Place agent far from obstacle to start
    start_x = 30.0
    start_y = 30.0
    engine.add_agent_b(start_x, start_y, cfg.agent_radius)
    engine.add_obstacle(CircleDef(cx=obs_cx, cy=obs_cy, radius=obs_radius))
    engine.set_velocity(vx, vy)

    min_dist = cfg.agent_radius + obs_radius
    tolerance = 0.5  # pymunk may allow slight overlap due to collision resolution

    for _ in range(n_steps):
        engine.step(dt=1.0)
        x, y = engine.get_agent_b_position()
        dist = math.sqrt((x - obs_cx) ** 2 + (y - obs_cy) ** 2)
        assert dist >= min_dist - tolerance, (
            f"Agent B penetrated circle obstacle: dist={dist:.4f}, "
            f"min_dist={min_dist:.4f}"
        )


# ---------------------------------------------------------------------------
# Property 7: Boundary Containment
# ---------------------------------------------------------------------------

# Feature: dec-pomdp-environment, Property 7: Boundary Containment
@settings(max_examples=100)
@given(
    start_x=st.floats(min_value=20.0, max_value=380.0),
    start_y=st.floats(min_value=20.0, max_value=280.0),
    vx=st.floats(min_value=-200.0, max_value=200.0),
    vy=st.floats(min_value=-200.0, max_value=200.0),
    n_steps=st.integers(min_value=1, max_value=30),
)
def test_prop_boundary_containment(
    start_x: float,
    start_y: float,
    vx: float,
    vy: float,
    n_steps: int,
) -> None:
    """Property 7: Boundary Containment.

    For any sequence of steps with a fixed initial velocity, Agent B's
    position shall satisfy:
      agent_radius ≤ x ≤ world_width − agent_radius  (± 0.1 tolerance)
      agent_radius ≤ y ≤ world_height − agent_radius  (± 0.1 tolerance)

    Velocity is set once; pymunk handles post-collision velocity naturally.

    Validates: Requirements 2.6, 4.4
    """
    cfg = _make_cfg()
    engine = PhysicsEngine(cfg)
    engine.add_agent_b(start_x, start_y, cfg.agent_radius)
    # Set velocity once — let pymunk handle collision response naturally
    engine.set_velocity(vx, vy)

    # Tolerance: pymunk resolves collisions with ~0.1 unit precision
    tolerance = 0.1

    for _ in range(n_steps):
        engine.step(dt=1.0)
        x, y = engine.get_agent_b_position()

        assert x >= cfg.agent_radius - tolerance, (
            f"x={x:.4f} < agent_radius={cfg.agent_radius} (left boundary violated)"
        )
        assert x <= cfg.world_width - cfg.agent_radius + tolerance, (
            f"x={x:.4f} > world_width - agent_radius={cfg.world_width - cfg.agent_radius} "
            f"(right boundary violated)"
        )
        assert y >= cfg.agent_radius - tolerance, (
            f"y={y:.4f} < agent_radius={cfg.agent_radius} (bottom boundary violated)"
        )
        assert y <= cfg.world_height - cfg.agent_radius + tolerance, (
            f"y={y:.4f} > world_height - agent_radius={cfg.world_height - cfg.agent_radius} "
            f"(top boundary violated)"
        )
