"""Unit tests for ProceduralGenerator (env/procedural_gen.py).

Covers:
- Correct entity types and counts
- All positions within grid bounds
- No two collidable entities at the same position
- AgentB position != Target position
- Seed reproducibility (same seed → same layout)
- Different seeds → different layouts
- min_separation=0 (no distance constraint)
- min_separation>0 enforces Manhattan distance between AgentB and Target
- GenerationFailedError raised when layout is impossible
"""

import pytest

from env.config_loader import EnvConfig
from env.errors import GenerationFailedError
from env.objects import AgentA, AgentB, Obstacle, Target
from env.procedural_gen import ProceduralGenerator


def make_config(
    grid_width: int = 10,
    grid_height: int = 10,
    num_obstacles: int = 5,
    random_seed: int = 0,
    max_steps: int = 200,
    tau: int = 1,
    min_separation: int = 0,
) -> EnvConfig:
    return EnvConfig(
        grid_width=grid_width,
        grid_height=grid_height,
        num_obstacles=num_obstacles,
        random_seed=random_seed,
        max_steps=max_steps,
        tau=tau,
        min_separation=min_separation,
    )


# ---------------------------------------------------------------------------
# Entity types and counts
# ---------------------------------------------------------------------------

def test_generate_returns_correct_entity_types_and_counts():
    cfg = make_config(num_obstacles=4)
    gen = ProceduralGenerator(cfg)
    entities = gen.generate(seed=1)

    agent_as = [e for e in entities if isinstance(e, AgentA)]
    agent_bs = [e for e in entities if isinstance(e, AgentB)]
    targets = [e for e in entities if isinstance(e, Target)]
    obstacles = [e for e in entities if isinstance(e, Obstacle)]

    assert len(agent_as) == 1
    assert len(agent_bs) == 1
    assert len(targets) == 1
    assert len(obstacles) == 4
    assert len(entities) == 7  # 1+1+1+4


def test_generate_zero_obstacles():
    cfg = make_config(num_obstacles=0)
    gen = ProceduralGenerator(cfg)
    entities = gen.generate(seed=42)
    obstacles = [e for e in entities if isinstance(e, Obstacle)]
    assert len(obstacles) == 0
    assert len(entities) == 3


def test_obstacle_ids_are_sequential():
    cfg = make_config(num_obstacles=3)
    gen = ProceduralGenerator(cfg)
    entities = gen.generate(seed=7)
    obs_ids = sorted(e.id for e in entities if isinstance(e, Obstacle))
    assert obs_ids == ["obstacle_0", "obstacle_1", "obstacle_2"]


# ---------------------------------------------------------------------------
# Grid bounds
# ---------------------------------------------------------------------------

def test_all_positions_within_grid_bounds():
    cfg = make_config(grid_width=8, grid_height=6, num_obstacles=6)
    gen = ProceduralGenerator(cfg)
    for seed in range(20):
        entities = gen.generate(seed=seed)
        for e in entities:
            assert 0 <= e.x < cfg.grid_width, f"x={e.x} out of bounds for {e.id}"
            assert 0 <= e.y < cfg.grid_height, f"y={e.y} out of bounds for {e.id}"


# ---------------------------------------------------------------------------
# No collidable overlap
# ---------------------------------------------------------------------------

def test_no_two_collidable_entities_share_position():
    cfg = make_config(num_obstacles=8)
    gen = ProceduralGenerator(cfg)
    for seed in range(20):
        entities = gen.generate(seed=seed)
        collidable = [e for e in entities if e.collidable]
        positions = [(e.x, e.y) for e in collidable]
        assert len(positions) == len(set(positions)), (
            f"Collidable overlap detected with seed={seed}"
        )


# ---------------------------------------------------------------------------
# AgentB != Target position
# ---------------------------------------------------------------------------

def test_agent_b_position_differs_from_target():
    cfg = make_config(num_obstacles=5)
    gen = ProceduralGenerator(cfg)
    for seed in range(30):
        entities = gen.generate(seed=seed)
        agent_b = next(e for e in entities if isinstance(e, AgentB))
        target = next(e for e in entities if isinstance(e, Target))
        assert (agent_b.x, agent_b.y) != (target.x, target.y), (
            f"AgentB == Target at seed={seed}"
        )


# ---------------------------------------------------------------------------
# Seed reproducibility
# ---------------------------------------------------------------------------

def test_same_seed_produces_identical_layout():
    cfg = make_config(num_obstacles=5)
    gen = ProceduralGenerator(cfg)
    for seed in [0, 1, 99, 12345]:
        entities_a = gen.generate(seed=seed)
        entities_b = gen.generate(seed=seed)
        positions_a = {e.id: (e.x, e.y) for e in entities_a}
        positions_b = {e.id: (e.x, e.y) for e in entities_b}
        assert positions_a == positions_b, f"Layouts differ for seed={seed}"


def test_same_seed_different_generator_instances_identical():
    """Two separate ProceduralGenerator instances with same config and seed."""
    cfg = make_config(num_obstacles=3)
    gen1 = ProceduralGenerator(cfg)
    gen2 = ProceduralGenerator(cfg)
    entities_1 = gen1.generate(seed=77)
    entities_2 = gen2.generate(seed=77)
    positions_1 = {e.id: (e.x, e.y) for e in entities_1}
    positions_2 = {e.id: (e.x, e.y) for e in entities_2}
    assert positions_1 == positions_2


# ---------------------------------------------------------------------------
# Different seeds → different layouts
# ---------------------------------------------------------------------------

def test_different_seeds_produce_different_layouts():
    cfg = make_config(grid_width=20, grid_height=20, num_obstacles=5)
    gen = ProceduralGenerator(cfg)
    seeds = list(range(10))
    layouts = []
    for seed in seeds:
        entities = gen.generate(seed=seed)
        layout = tuple(sorted((e.id, e.x, e.y) for e in entities))
        layouts.append(layout)
    # At least some layouts must differ (extremely unlikely all are identical)
    assert len(set(layouts)) > 1, "All seeds produced identical layouts"


# ---------------------------------------------------------------------------
# min_separation = 0 (no constraint)
# ---------------------------------------------------------------------------

def test_min_separation_zero_no_distance_constraint():
    """min_separation=0 should not impose any distance requirement."""
    cfg = make_config(num_obstacles=0, min_separation=0)
    gen = ProceduralGenerator(cfg)
    # Just verify it generates without error across many seeds
    for seed in range(20):
        entities = gen.generate(seed=seed)
        assert len(entities) == 3


# ---------------------------------------------------------------------------
# min_separation > 0
# ---------------------------------------------------------------------------

def test_min_separation_enforced():
    cfg = make_config(
        grid_width=20, grid_height=20, num_obstacles=3, min_separation=5
    )
    gen = ProceduralGenerator(cfg)
    for seed in range(30):
        entities = gen.generate(seed=seed)
        agent_b = next(e for e in entities if isinstance(e, AgentB))
        target = next(e for e in entities if isinstance(e, Target))
        dist = abs(agent_b.x - target.x) + abs(agent_b.y - target.y)
        assert dist >= 5, (
            f"min_separation violated: dist={dist} < 5 at seed={seed}"
        )


def test_min_separation_large_value():
    """Larger min_separation on a big grid should still succeed."""
    cfg = make_config(
        grid_width=64, grid_height=64, num_obstacles=0, min_separation=10
    )
    gen = ProceduralGenerator(cfg)
    for seed in range(10):
        entities = gen.generate(seed=seed)
        agent_b = next(e for e in entities if isinstance(e, AgentB))
        target = next(e for e in entities if isinstance(e, Target))
        dist = abs(agent_b.x - target.x) + abs(agent_b.y - target.y)
        assert dist >= 10


# ---------------------------------------------------------------------------
# GenerationFailedError
# ---------------------------------------------------------------------------

def test_generation_failed_error_raised_when_impossible():
    """A 1x1 grid with 1 obstacle is impossible to satisfy — should raise."""
    cfg = make_config(grid_width=1, grid_height=1, num_obstacles=1)
    gen = ProceduralGenerator(cfg)
    with pytest.raises(GenerationFailedError) as exc_info:
        gen.generate(seed=0)
    msg = str(exc_info.value)
    assert "seed" in msg.lower() or "0" in msg


def test_generation_failed_error_contains_seed_and_config():
    """Error message should include seed and config details."""
    cfg = make_config(grid_width=2, grid_height=2, num_obstacles=10)
    gen = ProceduralGenerator(cfg)
    with pytest.raises(GenerationFailedError) as exc_info:
        gen.generate(seed=999)
    msg = str(exc_info.value)
    assert "999" in msg  # seed present
