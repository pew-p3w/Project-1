"""Property-based tests for the Dec-POMDP environment step pipeline.

Covers Properties 15, 16, 17, 18, 19, 21.
Validates Requirements 11.1, 11.2, 11.3, 11.4, 11.5, 12.2, 12.3, 15.2.
"""

import json
import math
import os
import tempfile

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from env.environment import DecPOMDPEnvironment
from env.errors import EpisodeTerminatedError

# ---------------------------------------------------------------------------
# Base config and helpers
# ---------------------------------------------------------------------------

_BASE_CONFIG = {
    "world_width": 400.0,
    "world_height": 300.0,
    "agent_radius": 10.0,
    "max_speed": 200.0,
    "max_angular_velocity": 0.5,
    "capture_radius": 20.0,
    "random_seed": 42,
    "max_steps": 50,
    "tau": 0,
    "min_separation": 50.0,
    "obstacles": [],
    "render": False,
    "log_level": "WARNING",
}


def _write_config(cfg: dict) -> str:
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(cfg, f)
    return path


def _make_env(cfg: dict | None = None) -> tuple[DecPOMDPEnvironment, str]:
    config = dict(_BASE_CONFIG) if cfg is None else cfg
    path = _write_config(config)
    env = DecPOMDPEnvironment(path)
    return env, path


def _place_agent_b(env: DecPOMDPEnvironment, x: float, y: float) -> None:
    """Manually place agent_b at (x, y) in both entity and physics body."""
    env._agent_b.x = x
    env._agent_b.y = y
    env._physics._agent_b_body.position = (x, y)


# ---------------------------------------------------------------------------
# Property 15: Capture Triggers Positive Reward and Termination
# Validates: Requirements 11.1, 11.2
# ---------------------------------------------------------------------------

@given(
    offset_x=st.floats(min_value=-19.9, max_value=19.9, allow_nan=False, allow_infinity=False),
    offset_y=st.floats(min_value=-19.9, max_value=19.9, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50)
def test_prop_15_capture_triggers_positive_reward_and_termination(offset_x, offset_y):
    """Property 15: Capture Triggers Positive Reward and Termination

    # Feature: dec-pomdp-environment, Property 15: Capture Triggers Positive Reward and Termination
    **Validates: Requirements 11.1, 11.2**
    """
    dist = math.hypot(offset_x, offset_y)
    assume(dist <= 19.9)  # strictly within capture_radius=20.0

    env, path = _make_env()
    try:
        env.reset()
        target_x = env._target.x
        target_y = env._target.y
        new_x = target_x + offset_x
        new_y = target_y + offset_y
        # Clamp to world bounds
        new_x = max(env._config.agent_radius, min(env._config.world_width - env._config.agent_radius, new_x))
        new_y = max(env._config.agent_radius, min(env._config.world_height - env._config.agent_radius, new_y))
        _place_agent_b(env, new_x, new_y)
        result = env.step((0.0, 0.0), [0.0] * 16)
        assert result.reward > 0, f"Expected reward > 0 for capture, got {result.reward}"
        assert result.terminated is True
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Property 16: No-Capture Steps Return Zero Reward
# Validates: Requirement 11.4
# ---------------------------------------------------------------------------

@given(n=st.integers(min_value=1, max_value=20))
@settings(max_examples=50)
def test_prop_16_no_capture_steps_return_zero_reward(n):
    """Property 16: No-Capture Steps Return Zero Reward

    # Feature: dec-pomdp-environment, Property 16: No-Capture Steps Return Zero Reward
    **Validates: Requirement 11.4**
    """
    # Use large max_steps so timeout doesn't interfere
    cfg = dict(_BASE_CONFIG)
    cfg["max_steps"] = 100
    cfg["min_separation"] = 80.0  # keep agent_b far from target
    env, path = _make_env(cfg)
    try:
        env.reset()
        # Place agent_b far from target (center of world, target is elsewhere)
        # min_separation=80 guarantees initial distance >= 80 > capture_radius=20
        for i in range(n):
            result = env.step((0.0, 0.0), [0.0] * 16)
            # Only check non-terminated steps
            if not result.terminated:
                assert result.reward == 0.0, (
                    f"Step {i+1}: expected reward == 0 for non-capture, got {result.reward}"
                )
            else:
                # If it terminated (timeout), reward must still be 0
                assert result.reward == 0.0
                break
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Property 17: Timeout Terminates with Zero Reward
# Validates: Requirement 11.3
# ---------------------------------------------------------------------------

@given(max_steps=st.integers(min_value=1, max_value=5))
@settings(max_examples=50)
def test_prop_17_timeout_terminates_with_zero_reward(max_steps):
    """Property 17: Timeout Terminates with Zero Reward

    # Feature: dec-pomdp-environment, Property 17: Timeout Terminates with Zero Reward
    **Validates: Requirement 11.3**
    """
    cfg = dict(_BASE_CONFIG)
    cfg["max_steps"] = max_steps
    cfg["min_separation"] = 50.0
    env, path = _make_env(cfg)
    try:
        env.reset()
        result = None
        for _ in range(max_steps):
            result = env.step((0.0, 0.0), [0.0] * 16)
            if result.terminated:
                break
        assert result is not None
        assert result.terminated is True, f"Expected terminated after {max_steps} steps"
        assert result.reward == 0.0, f"Expected reward == 0 on timeout, got {result.reward}"
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Property 18: Step on Terminated Episode Raises Error
# Validates: Requirements 11.5, 12.2
# ---------------------------------------------------------------------------

@given(max_steps=st.integers(min_value=1, max_value=3))
@settings(max_examples=30)
def test_prop_18_step_on_terminated_raises_error(max_steps):
    """Property 18: Step on Terminated Episode Raises Error

    # Feature: dec-pomdp-environment, Property 18: Step on Terminated Episode Raises Error
    **Validates: Requirements 11.5, 12.2**
    """
    cfg = dict(_BASE_CONFIG)
    cfg["max_steps"] = max_steps
    env, path = _make_env(cfg)
    try:
        env.reset()
        # Run until timeout
        for _ in range(max_steps):
            env.step((0.0, 0.0), [0.0] * 16)
        # Now episode is terminated — next step must raise
        with pytest.raises(EpisodeTerminatedError):
            env.step((0.0, 0.0), [0.0] * 16)
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Property 19: Timestep Increments by One Per Step
# Validates: Requirement 12.3
# ---------------------------------------------------------------------------

@given(n=st.integers(min_value=1, max_value=30))
@settings(max_examples=50)
def test_prop_19_timestep_increments_by_one_per_step(n):
    """Property 19: Timestep Increments by One Per Step

    # Feature: dec-pomdp-environment, Property 19: Timestep Increments by One Per Step
    **Validates: Requirement 12.3**
    """
    cfg = dict(_BASE_CONFIG)
    cfg["max_steps"] = max(n + 5, 50)  # ensure no timeout before n steps
    env, path = _make_env(cfg)
    try:
        env.reset()
        assert env.timestep == 0
        for i in range(n):
            env.step((0.0, 0.0), [0.0] * 16)
        assert env.timestep == n, f"Expected timestep == {n}, got {env.timestep}"
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Property 21: State Dict Reflects Current Entity Positions and Velocity
# Validates: Requirement 15.2
# ---------------------------------------------------------------------------

@given(n=st.integers(min_value=1, max_value=10))
@settings(max_examples=50)
def test_prop_21_state_dict_reflects_entity_positions_and_velocity(n):
    """Property 21: State Dict Reflects Current Entity Positions and Velocity

    # Feature: dec-pomdp-environment, Property 21: State Dict Reflects Current Entity Positions and Velocity
    **Validates: Requirement 15.2**
    """
    cfg = dict(_BASE_CONFIG)
    cfg["max_steps"] = max(n + 5, 50)
    env, path = _make_env(cfg)
    try:
        env.reset()
        for _ in range(n):
            result = env.step((0.0, 0.0), [0.0] * 16)
            if result.terminated:
                break
        sd = env.state_dict()
        # state_dict agent_b position must match direct entity query
        assert sd["agent_b"] == (env._agent_b.x, env._agent_b.y), (
            f"state_dict agent_b {sd['agent_b']} != entity ({env._agent_b.x}, {env._agent_b.y})"
        )
        # state_dict agent_b_velocity must match direct entity query
        assert sd["agent_b_velocity"] == (env._agent_b.vx, env._agent_b.vy), (
            f"state_dict velocity {sd['agent_b_velocity']} != entity ({env._agent_b.vx}, {env._agent_b.vy})"
        )
    finally:
        os.unlink(path)
