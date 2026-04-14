"""Property-based tests for ProceduralGenerator.

# Feature: dec-pomdp-environment

Properties covered:
  P2: Reproducibility — Same Seed Produces Identical Layout
  P3: All Entities Within World Bounds After Reset
  P8: Initialization Separation Invariant
  P9: Minimum Separation Enforced
"""

from __future__ import annotations

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from env.config_loader import EnvConfig
from env.procedural_gen import ProceduralGenerator


# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

_BASE_CONFIG = dict(
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


def _make_config(**overrides) -> EnvConfig:
    d = dict(_BASE_CONFIG)
    d.update(overrides)
    return EnvConfig(**d)


def _dist(layout, attr_a: str, attr_b: str) -> float:
    a = getattr(layout, attr_a)
    b = getattr(layout, attr_b)
    return math.hypot(a.x - b.x, a.y - b.y)


# ---------------------------------------------------------------------------
# Property 2: Reproducibility — Same Seed Produces Identical Layout
# Validates: Requirements 1.6, 7.3, 7.4, 13.4
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(seed=st.integers(min_value=0, max_value=2**31 - 1))
def test_prop_reproducibility_same_seed(seed):
    # Feature: dec-pomdp-environment, Property 2: Reproducibility — Same Seed Produces Identical Layout
    cfg = _make_config()
    gen = ProceduralGenerator(cfg)
    layout1 = gen.generate(seed=seed)
    layout2 = gen.generate(seed=seed)

    assert layout1.agent_a.x == layout2.agent_a.x
    assert layout1.agent_a.y == layout2.agent_a.y
    assert layout1.agent_b.x == layout2.agent_b.x
    assert layout1.agent_b.y == layout2.agent_b.y
    assert layout1.target.x == layout2.target.x
    assert layout1.target.y == layout2.target.y


# ---------------------------------------------------------------------------
# Property 3: All Entities Within World Bounds After Reset
# Validates: Requirements 2.1, 7.1
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(seed=st.integers(min_value=0, max_value=2**31 - 1))
def test_prop_entities_within_world_bounds(seed):
    # Feature: dec-pomdp-environment, Property 3: All Entities Within World Bounds After Reset
    cfg = _make_config()
    gen = ProceduralGenerator(cfg)
    layout = gen.generate(seed=seed)

    margin = cfg.agent_radius
    for entity in [layout.agent_a, layout.agent_b, layout.target]:
        assert margin <= entity.x <= cfg.world_width - margin, (
            f"{entity.id}.x={entity.x} out of [{margin}, {cfg.world_width - margin}]"
        )
        assert margin <= entity.y <= cfg.world_height - margin, (
            f"{entity.id}.y={entity.y} out of [{margin}, {cfg.world_height - margin}]"
        )


# ---------------------------------------------------------------------------
# Property 8: Initialization Separation Invariant
# Validates: Requirements 7.5
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(seed=st.integers(min_value=0, max_value=2**31 - 1))
def test_prop_init_separation_exceeds_capture_radius(seed):
    # Feature: dec-pomdp-environment, Property 8: Initialization Separation Invariant
    cfg = _make_config(capture_radius=20.0)
    gen = ProceduralGenerator(cfg)
    layout = gen.generate(seed=seed)

    d = math.hypot(layout.agent_b.x - layout.target.x, layout.agent_b.y - layout.target.y)
    assert d > cfg.capture_radius, (
        f"dist(AgentB, Target)={d} not > capture_radius={cfg.capture_radius}"
    )


# ---------------------------------------------------------------------------
# Property 9: Minimum Separation Enforced
# Validates: Requirements 7.6
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(
    seed=st.integers(min_value=0, max_value=2**31 - 1),
    min_sep=st.floats(min_value=30.0, max_value=100.0),
)
def test_prop_min_separation_enforced(seed, min_sep):
    # Feature: dec-pomdp-environment, Property 9: Minimum Separation Enforced
    cfg = _make_config(
        world_width=400.0,
        world_height=300.0,
        agent_radius=10.0,
        capture_radius=20.0,
        min_separation=min_sep,
    )
    gen = ProceduralGenerator(cfg)
    layout = gen.generate(seed=seed)

    d = math.hypot(layout.agent_b.x - layout.target.x, layout.agent_b.y - layout.target.y)
    assert d >= min_sep, (
        f"dist(AgentB, Target)={d} < min_separation={min_sep}"
    )
