"""Unit tests for reward, termination, and step pipeline.

Tests cover Requirements 11.1, 11.2, 11.3, 11.4, 11.5, 12.1, 12.2, 12.3, 15.2.
"""

import json
import math
import os
import tempfile

import pytest

from env.environment import DecPOMDPEnvironment
from env.errors import EpisodeTerminatedError

# ---------------------------------------------------------------------------
# Helper config
# ---------------------------------------------------------------------------

_BASE_CONFIG = {
    "world_width": 400.0,
    "world_height": 300.0,
    "agent_radius": 10.0,
    "max_speed": 200.0,
    "max_angular_velocity": 0.5,
    "capture_radius": 20.0,
    "random_seed": 42,
    "max_steps": 10,
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


def _place_agent_b_at_target(env: DecPOMDPEnvironment) -> None:
    """Manually place agent_b at the target position (both entity and physics body)."""
    env._agent_b.x = env._target.x
    env._agent_b.y = env._target.y
    env._physics._agent_b_body.position = (env._target.x, env._target.y)


# ---------------------------------------------------------------------------
# Test 1: Capture — agent_b at target position → reward > 0, terminated == True
# ---------------------------------------------------------------------------

def test_capture_at_target_position():
    """Placing agent_b exactly at target and stepping yields reward > 0 and terminated."""
    env, path = _make_env()
    try:
        env.reset()
        _place_agent_b_at_target(env)
        result = env.step((0.0, 0.0), [0.0] * 16)
        assert result.reward > 0, f"Expected reward > 0, got {result.reward}"
        assert result.terminated is True
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Test 2: Capture at exact capture_radius distance → reward > 0, terminated == True
# ---------------------------------------------------------------------------

def test_capture_at_exact_capture_radius():
    """Placing agent_b exactly at capture_radius from target triggers capture."""
    env, path = _make_env()
    try:
        env.reset()
        capture_radius = env._config.capture_radius
        # Place agent_b exactly capture_radius away from target (along x-axis)
        env._agent_b.x = env._target.x + capture_radius
        env._agent_b.y = env._target.y
        env._physics._agent_b_body.position = (env._agent_b.x, env._agent_b.y)
        result = env.step((0.0, 0.0), [0.0] * 16)
        assert result.reward > 0, f"Expected reward > 0 at exact capture_radius, got {result.reward}"
        assert result.terminated is True
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Test 3: Just outside capture_radius → reward == 0, terminated == False
# ---------------------------------------------------------------------------

def test_just_outside_capture_radius_no_capture():
    """Placing agent_b just outside capture_radius does not trigger capture."""
    env, path = _make_env()
    try:
        env.reset()
        capture_radius = env._config.capture_radius
        # Place agent_b slightly beyond capture_radius
        env._agent_b.x = env._target.x + capture_radius + 1.0
        env._agent_b.y = env._target.y
        env._physics._agent_b_body.position = (env._agent_b.x, env._agent_b.y)
        result = env.step((0.0, 0.0), [0.0] * 16)
        assert result.reward == 0.0, f"Expected reward == 0, got {result.reward}"
        assert result.terminated is False
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Test 4: Timeout — max_steps=3, run 3 steps without capture → terminated, reward == 0
# ---------------------------------------------------------------------------

def test_timeout_terminates_with_zero_reward():
    """After max_steps steps without capture, episode terminates with reward == 0."""
    cfg = dict(_BASE_CONFIG)
    cfg["max_steps"] = 3
    env, path = _make_env(cfg)
    try:
        env.reset()
        result = None
        for _ in range(3):
            result = env.step((0.0, 0.0), [0.0] * 16)
        assert result.terminated is True
        assert result.reward == 0.0
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Test 5: Ongoing — single step far from target → reward == 0, terminated == False
# ---------------------------------------------------------------------------

def test_ongoing_step_far_from_target():
    """A single step far from the target returns reward == 0 and terminated == False."""
    env, path = _make_env()
    try:
        env.reset()
        # Ensure agent_b is far from target (min_separation=50 guarantees this at reset)
        result = env.step((0.0, 0.0), [0.0] * 16)
        assert result.reward == 0.0
        assert result.terminated is False
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Test 6: After capture, step() raises EpisodeTerminatedError
# ---------------------------------------------------------------------------

def test_step_after_capture_raises_error():
    """Calling step() after a capture termination raises EpisodeTerminatedError."""
    env, path = _make_env()
    try:
        env.reset()
        _place_agent_b_at_target(env)
        env.step((0.0, 0.0), [0.0] * 16)  # capture step
        with pytest.raises(EpisodeTerminatedError):
            env.step((0.0, 0.0), [0.0] * 16)
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Test 7: After timeout, step() raises EpisodeTerminatedError
# ---------------------------------------------------------------------------

def test_step_after_timeout_raises_error():
    """Calling step() after a timeout termination raises EpisodeTerminatedError."""
    cfg = dict(_BASE_CONFIG)
    cfg["max_steps"] = 2
    env, path = _make_env(cfg)
    try:
        env.reset()
        for _ in range(2):
            env.step((0.0, 0.0), [0.0] * 16)
        with pytest.raises(EpisodeTerminatedError):
            env.step((0.0, 0.0), [0.0] * 16)
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Test 8: state_dict()["last_reward"] == 1.0 after capture
# ---------------------------------------------------------------------------

def test_state_dict_last_reward_after_capture():
    """state_dict()['last_reward'] should be 1.0 after a capture step."""
    env, path = _make_env()
    try:
        env.reset()
        _place_agent_b_at_target(env)
        env.step((0.0, 0.0), [0.0] * 16)
        sd = env.state_dict()
        assert sd["last_reward"] == 1.0
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Test 9: state_dict()["terminated"] == True after capture
# ---------------------------------------------------------------------------

def test_state_dict_terminated_after_capture():
    """state_dict()['terminated'] should be True after a capture step."""
    env, path = _make_env()
    try:
        env.reset()
        _place_agent_b_at_target(env)
        env.step((0.0, 0.0), [0.0] * 16)
        sd = env.state_dict()
        assert sd["terminated"] is True
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Test 10: state_dict()["terminated"] == True after timeout
# ---------------------------------------------------------------------------

def test_state_dict_terminated_after_timeout():
    """state_dict()['terminated'] should be True after timeout."""
    cfg = dict(_BASE_CONFIG)
    cfg["max_steps"] = 2
    env, path = _make_env(cfg)
    try:
        env.reset()
        for _ in range(2):
            env.step((0.0, 0.0), [0.0] * 16)
        sd = env.state_dict()
        assert sd["terminated"] is True
    finally:
        os.unlink(path)
