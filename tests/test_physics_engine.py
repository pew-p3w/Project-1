"""Unit tests for PhysicsEngine (env/physics_engine.py).

Covers:
- Initialization without error
- Boundary walls created (static shapes in space after init)
- add_agent_b creates a body at the correct position
- get_agent_b_position returns the position set by add_agent_b
- set_velocity sets velocity on Agent B's body
- get_agent_b_velocity returns the velocity after set_velocity
- step() advances simulation without error
- Agent B moves in the direction of velocity after step()
- add_obstacle with RectDef registers without error
- add_obstacle with CircleDef registers without error
- add_obstacle with PolygonDef registers without error
- reset() clears Agent B body (get_agent_b_position raises after reset)
- Agent B is blocked by a wall (stays within bounds)
"""

import math
import pytest

from env.config_loader import EnvConfig
from env.objects import CircleDef, PolygonDef, RectDef
from env.physics_engine import PhysicsEngine


# ---------------------------------------------------------------------------
# Minimal config fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def cfg() -> EnvConfig:
    return EnvConfig(
        world_width=400.0,
        world_height=300.0,
        agent_radius=10.0,
        max_speed=200.0,
        max_angular_velocity=0.3,
        capture_radius=15.0,
        random_seed=0,
        max_steps=100,
        tau=1,
    )


@pytest.fixture
def engine(cfg: EnvConfig) -> PhysicsEngine:
    return PhysicsEngine(cfg)


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def test_init_no_error(cfg: EnvConfig) -> None:
    """PhysicsEngine initializes without raising."""
    pe = PhysicsEngine(cfg)
    assert pe is not None


def test_boundary_walls_created(engine: PhysicsEngine) -> None:
    """Space has static shapes (boundary walls) after init."""
    # Count shapes in the space — should be exactly 4 boundary segments
    assert len(engine._space.shapes) == 4, "Expected 4 boundary wall segments"


# ---------------------------------------------------------------------------
# Agent B body
# ---------------------------------------------------------------------------

def test_add_agent_b_creates_body(engine: PhysicsEngine) -> None:
    """add_agent_b creates a body in the space."""
    engine.add_agent_b(100.0, 150.0, 10.0)
    assert engine._agent_b_body is not None


def test_get_agent_b_position_after_add(engine: PhysicsEngine) -> None:
    """get_agent_b_position returns the position passed to add_agent_b."""
    engine.add_agent_b(100.0, 150.0, 10.0)
    x, y = engine.get_agent_b_position()
    assert abs(x - 100.0) < 1e-6
    assert abs(y - 150.0) < 1e-6


def test_get_agent_b_position_raises_without_body(engine: PhysicsEngine) -> None:
    """get_agent_b_position raises RuntimeError if Agent B not added."""
    with pytest.raises(RuntimeError):
        engine.get_agent_b_position()


# ---------------------------------------------------------------------------
# Velocity
# ---------------------------------------------------------------------------

def test_set_velocity(engine: PhysicsEngine) -> None:
    """set_velocity sets velocity on Agent B's body without error."""
    engine.add_agent_b(200.0, 150.0, 10.0)
    engine.set_velocity(50.0, -30.0)  # should not raise


def test_get_agent_b_velocity_after_set(engine: PhysicsEngine) -> None:
    """get_agent_b_velocity returns the velocity set by set_velocity."""
    engine.add_agent_b(200.0, 150.0, 10.0)
    engine.set_velocity(50.0, -30.0)
    vx, vy = engine.get_agent_b_velocity()
    assert abs(vx - 50.0) < 1e-6
    assert abs(vy - (-30.0)) < 1e-6


def test_set_velocity_raises_without_body(engine: PhysicsEngine) -> None:
    """set_velocity raises RuntimeError if Agent B not added."""
    with pytest.raises(RuntimeError):
        engine.set_velocity(10.0, 10.0)


# ---------------------------------------------------------------------------
# Step
# ---------------------------------------------------------------------------

def test_step_no_error(engine: PhysicsEngine) -> None:
    """step() advances simulation without raising."""
    engine.add_agent_b(200.0, 150.0, 10.0)
    engine.set_velocity(10.0, 0.0)
    engine.step()  # should not raise


def test_agent_b_moves_after_step(engine: PhysicsEngine) -> None:
    """Agent B moves in the direction of velocity after step()."""
    engine.add_agent_b(200.0, 150.0, 10.0)
    engine.set_velocity(50.0, 0.0)
    engine.step(dt=1.0)
    x, y = engine.get_agent_b_position()
    # Should have moved right
    assert x > 200.0


def test_agent_b_moves_vertically(engine: PhysicsEngine) -> None:
    """Agent B moves upward when given positive vy."""
    engine.add_agent_b(200.0, 150.0, 10.0)
    engine.set_velocity(0.0, 50.0)
    engine.step(dt=1.0)
    x, y = engine.get_agent_b_position()
    assert y > 150.0


# ---------------------------------------------------------------------------
# Obstacles
# ---------------------------------------------------------------------------

def test_add_obstacle_rect(engine: PhysicsEngine) -> None:
    """add_obstacle with RectDef registers without error."""
    rect = RectDef(cx=200.0, cy=150.0, width=40.0, height=20.0, angle=0.0)
    engine.add_obstacle(rect)
    assert len(engine._obstacle_bodies) == 1


def test_add_obstacle_circle(engine: PhysicsEngine) -> None:
    """add_obstacle with CircleDef registers without error."""
    circle = CircleDef(cx=100.0, cy=100.0, radius=20.0)
    engine.add_obstacle(circle)
    assert len(engine._obstacle_bodies) == 1


def test_add_obstacle_polygon(engine: PhysicsEngine) -> None:
    """add_obstacle with PolygonDef registers without error."""
    poly = PolygonDef(vertices=[(300.0, 100.0), (350.0, 150.0), (280.0, 160.0)])
    engine.add_obstacle(poly)
    assert len(engine._obstacle_bodies) == 1


def test_add_multiple_obstacles(engine: PhysicsEngine) -> None:
    """Multiple obstacles can be added without error."""
    engine.add_obstacle(RectDef(cx=100.0, cy=100.0, width=30.0, height=20.0, angle=0.0))
    engine.add_obstacle(CircleDef(cx=200.0, cy=200.0, radius=15.0))
    engine.add_obstacle(PolygonDef(vertices=[(300.0, 100.0), (350.0, 150.0), (280.0, 160.0)]))
    assert len(engine._obstacle_bodies) == 3


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

def test_reset_clears_agent_b(engine: PhysicsEngine) -> None:
    """reset() removes Agent B; get_agent_b_position raises afterwards."""
    engine.add_agent_b(200.0, 150.0, 10.0)
    engine.reset()
    with pytest.raises(RuntimeError):
        engine.get_agent_b_position()


def test_reset_clears_obstacles(engine: PhysicsEngine) -> None:
    """reset() removes all obstacle bodies."""
    engine.add_obstacle(RectDef(cx=100.0, cy=100.0, width=30.0, height=20.0, angle=0.0))
    engine.add_obstacle(CircleDef(cx=200.0, cy=200.0, radius=15.0))
    engine.reset()
    assert len(engine._obstacle_bodies) == 0


def test_reset_recreates_boundary_walls(engine: PhysicsEngine) -> None:
    """reset() recreates the 4 boundary wall segments."""
    engine.reset()
    assert len(engine._space.shapes) == 4


def test_reset_allows_readd_agent_b(engine: PhysicsEngine) -> None:
    """After reset(), add_agent_b can be called again successfully."""
    engine.add_agent_b(200.0, 150.0, 10.0)
    engine.reset()
    engine.add_agent_b(50.0, 50.0, 10.0)
    x, y = engine.get_agent_b_position()
    assert abs(x - 50.0) < 1e-6
    assert abs(y - 50.0) < 1e-6


# ---------------------------------------------------------------------------
# Boundary containment
# ---------------------------------------------------------------------------

def test_agent_b_blocked_by_right_wall(engine: PhysicsEngine, cfg: EnvConfig) -> None:
    """Agent B stays within world bounds when driven toward the right wall."""
    # Place near right wall, drive right
    start_x = cfg.world_width - cfg.agent_radius - 5.0
    engine.add_agent_b(start_x, cfg.world_height / 2, cfg.agent_radius)
    engine.set_velocity(200.0, 0.0)
    for _ in range(50):
        engine.step(dt=1.0)
    x, y = engine.get_agent_b_position()
    assert x <= cfg.world_width, f"Agent B escaped right wall: x={x}"


def test_agent_b_blocked_by_left_wall(engine: PhysicsEngine, cfg: EnvConfig) -> None:
    """Agent B stays within world bounds when driven toward the left wall."""
    engine.add_agent_b(cfg.agent_radius + 5.0, cfg.world_height / 2, cfg.agent_radius)
    engine.set_velocity(-200.0, 0.0)
    for _ in range(50):
        engine.step(dt=1.0)
    x, y = engine.get_agent_b_position()
    assert x >= 0.0, f"Agent B escaped left wall: x={x}"


def test_agent_b_blocked_by_top_wall(engine: PhysicsEngine, cfg: EnvConfig) -> None:
    """Agent B stays within world bounds when driven toward the top wall."""
    engine.add_agent_b(cfg.world_width / 2, cfg.world_height - cfg.agent_radius - 5.0, cfg.agent_radius)
    engine.set_velocity(0.0, 200.0)
    for _ in range(50):
        engine.step(dt=1.0)
    x, y = engine.get_agent_b_position()
    assert y <= cfg.world_height, f"Agent B escaped top wall: y={y}"


def test_agent_b_blocked_by_bottom_wall(engine: PhysicsEngine, cfg: EnvConfig) -> None:
    """Agent B stays within world bounds when driven toward the bottom wall."""
    engine.add_agent_b(cfg.world_width / 2, cfg.agent_radius + 5.0, cfg.agent_radius)
    engine.set_velocity(0.0, -200.0)
    for _ in range(50):
        engine.step(dt=1.0)
    x, y = engine.get_agent_b_position()
    assert y >= 0.0, f"Agent B escaped bottom wall: y={y}"
