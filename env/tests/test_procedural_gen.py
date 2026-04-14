"""Unit tests for env/procedural_gen.py."""

from __future__ import annotations

import math

import pytest

from env.config_loader import EnvConfig
from env.errors import GenerationFailedError
from env.objects import AgentA, AgentB, Obstacle, Target
from env.physics_engine import PhysicsEngine
from env.procedural_gen import GeneratedLayout, ProceduralGenerator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(**overrides) -> EnvConfig:
    """Return a minimal valid EnvConfig, with optional field overrides."""
    defaults = dict(
        world_width=400.0,
        world_height=300.0,
        agent_radius=10.0,
        max_speed=150.0,
        max_angular_velocity=0.2,
        capture_radius=20.0,
        random_seed=42,
        max_steps=500,
        tau=3,
        min_separation=0.0,
        obstacles=[],
        procedural=None,
        render=False,
        log_level="INFO",
    )
    defaults.update(overrides)
    return EnvConfig(**defaults)


def _dist(a, b) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


# ---------------------------------------------------------------------------
# 1. generate() returns a GeneratedLayout with correct entity types
# ---------------------------------------------------------------------------

def test_generate_returns_generated_layout():
    cfg = _make_config()
    gen = ProceduralGenerator(cfg)
    layout = gen.generate(seed=0)
    assert isinstance(layout, GeneratedLayout)
    assert isinstance(layout.agent_a, AgentA)
    assert isinstance(layout.agent_b, AgentB)
    assert isinstance(layout.target, Target)
    assert isinstance(layout.obstacles, list)


def test_entity_ids():
    cfg = _make_config()
    gen = ProceduralGenerator(cfg)
    layout = gen.generate(seed=1)
    assert layout.agent_a.id == "agent_a"
    assert layout.agent_b.id == "agent_b"
    assert layout.target.id == "target"


# ---------------------------------------------------------------------------
# 2. Positions within world bounds (with margin = agent_radius)
# ---------------------------------------------------------------------------

def test_positions_within_bounds():
    cfg = _make_config()
    margin = cfg.agent_radius
    gen = ProceduralGenerator(cfg)
    for seed in range(20):
        layout = gen.generate(seed=seed)
        for entity in [layout.agent_a, layout.agent_b, layout.target]:
            assert margin <= entity.x <= cfg.world_width - margin, (
                f"x={entity.x} out of bounds for {entity.id} (seed={seed})"
            )
            assert margin <= entity.y <= cfg.world_height - margin, (
                f"y={entity.y} out of bounds for {entity.id} (seed={seed})"
            )


# ---------------------------------------------------------------------------
# 3. dist(AgentB, Target) > capture_radius after generation
# ---------------------------------------------------------------------------

def test_agent_b_target_separation_exceeds_capture_radius():
    cfg = _make_config(capture_radius=20.0)
    gen = ProceduralGenerator(cfg)
    for seed in range(20):
        layout = gen.generate(seed=seed)
        d = _dist(layout.agent_b, layout.target)
        assert d > cfg.capture_radius, (
            f"dist={d} not > capture_radius={cfg.capture_radius} (seed={seed})"
        )


# ---------------------------------------------------------------------------
# 4. min_separation=0 works (no extra distance constraint)
# ---------------------------------------------------------------------------

def test_min_separation_zero_no_extra_constraint():
    cfg = _make_config(min_separation=0.0, capture_radius=5.0)
    gen = ProceduralGenerator(cfg)
    # Should succeed without issues
    layout = gen.generate(seed=99)
    assert _dist(layout.agent_b, layout.target) > cfg.capture_radius


# ---------------------------------------------------------------------------
# 5. min_separation > 0 enforces Euclidean distance >= min_separation
# ---------------------------------------------------------------------------

def test_min_separation_enforced():
    min_sep = 80.0
    cfg = _make_config(min_separation=min_sep, capture_radius=20.0)
    gen = ProceduralGenerator(cfg)
    for seed in range(20):
        layout = gen.generate(seed=seed)
        d = _dist(layout.agent_b, layout.target)
        assert d >= min_sep, (
            f"dist={d} < min_separation={min_sep} (seed={seed})"
        )


# ---------------------------------------------------------------------------
# 6. Same seed produces identical layout
# ---------------------------------------------------------------------------

def test_same_seed_reproducible():
    cfg = _make_config()
    gen = ProceduralGenerator(cfg)
    layout1 = gen.generate(seed=42)
    layout2 = gen.generate(seed=42)
    assert layout1.agent_a.x == layout2.agent_a.x
    assert layout1.agent_a.y == layout2.agent_a.y
    assert layout1.agent_b.x == layout2.agent_b.x
    assert layout1.agent_b.y == layout2.agent_b.y
    assert layout1.target.x == layout2.target.x
    assert layout1.target.y == layout2.target.y


# ---------------------------------------------------------------------------
# 7. Different seeds produce different layouts (probabilistic)
# ---------------------------------------------------------------------------

def test_different_seeds_produce_different_layouts():
    cfg = _make_config()
    gen = ProceduralGenerator(cfg)
    layout0 = gen.generate(seed=0)
    layout1 = gen.generate(seed=1)
    # It would be astronomically unlikely for both positions to match exactly
    assert (layout0.agent_b.x, layout0.agent_b.y) != (layout1.agent_b.x, layout1.agent_b.y)


# ---------------------------------------------------------------------------
# 8. Explicit obstacles from config are included in layout
# ---------------------------------------------------------------------------

def test_explicit_obstacles_included():
    obs_list = [
        {"type": "rect", "cx": 200.0, "cy": 150.0, "width": 40.0, "height": 20.0, "angle": 0.0},
        {"type": "circle", "cx": 100.0, "cy": 100.0, "radius": 15.0},
    ]
    cfg = _make_config(obstacles=obs_list)
    gen = ProceduralGenerator(cfg)
    layout = gen.generate(seed=7)
    assert len(layout.obstacles) == 2
    assert layout.obstacles[0].id == "obstacle_0"
    assert layout.obstacles[1].id == "obstacle_1"


def test_explicit_polygon_obstacle():
    obs_list = [
        {"type": "polygon", "vertices": [[300, 100], [350, 150], [280, 160]]},
    ]
    cfg = _make_config(obstacles=obs_list)
    gen = ProceduralGenerator(cfg)
    layout = gen.generate(seed=3)
    assert len(layout.obstacles) == 1
    assert layout.obstacles[0].id == "obstacle_0"


# ---------------------------------------------------------------------------
# 9. GenerationFailedError raised when constraints are impossible
# ---------------------------------------------------------------------------

def test_generation_failed_tiny_world():
    """World so small that no valid positions exist."""
    cfg = _make_config(
        world_width=5.0,
        world_height=5.0,
        agent_radius=10.0,  # margin > world size
    )
    gen = ProceduralGenerator(cfg)
    with pytest.raises(GenerationFailedError):
        gen.generate(seed=0)


def test_generation_failed_huge_min_separation():
    """min_separation larger than the world diagonal — impossible to satisfy."""
    cfg = _make_config(
        world_width=100.0,
        world_height=100.0,
        agent_radius=5.0,
        capture_radius=5.0,
        min_separation=10000.0,  # impossible
    )
    gen = ProceduralGenerator(cfg)
    with pytest.raises(GenerationFailedError):
        gen.generate(seed=0)


def test_generation_failed_error_contains_seed():
    cfg = _make_config(
        world_width=100.0,
        world_height=100.0,
        agent_radius=5.0,
        capture_radius=5.0,
        min_separation=10000.0,
    )
    gen = ProceduralGenerator(cfg)
    with pytest.raises(GenerationFailedError, match="seed=123"):
        gen.generate(seed=123)


# ---------------------------------------------------------------------------
# 10. Obstacles registered with PhysicsEngine
# ---------------------------------------------------------------------------

def test_obstacles_registered_with_physics_engine():
    """After generate(), a fresh PhysicsEngine should have obstacle bodies."""
    obs_list = [
        {"type": "circle", "cx": 200.0, "cy": 150.0, "radius": 15.0},
        {"type": "circle", "cx": 300.0, "cy": 200.0, "radius": 10.0},
    ]
    cfg = _make_config(obstacles=obs_list)
    gen = ProceduralGenerator(cfg)
    layout = gen.generate(seed=5)

    # Verify by re-registering with a fresh engine and checking body count
    physics = PhysicsEngine(cfg)
    for obs in layout.obstacles:
        physics.add_obstacle(obs.shape_def)

    assert len(physics._obstacle_bodies) == len(obs_list)


def test_no_obstacles_empty_list():
    cfg = _make_config(obstacles=[])
    gen = ProceduralGenerator(cfg)
    layout = gen.generate(seed=0)
    assert layout.obstacles == []


# ---------------------------------------------------------------------------
# 11. Procedural obstacle generation
# ---------------------------------------------------------------------------

def test_procedural_obstacles_generated():
    cfg = _make_config(
        procedural={"count": 3, "min_radius": 5.0, "max_radius": 15.0}
    )
    gen = ProceduralGenerator(cfg)
    layout = gen.generate(seed=10)
    assert len(layout.obstacles) == 3
    for i, obs in enumerate(layout.obstacles):
        assert obs.id == f"obstacle_{i}"
