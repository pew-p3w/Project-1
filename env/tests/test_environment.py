"""Unit tests for DecPOMDPEnvironment — Tasks 8 & 9: Observation interface and step pipeline.

Tests cover:
- __init__ loads config without error
- reset() returns a 2-tuple
- reset() obs_a has all required keys
- reset() obs_b is {}
- obs_a["timestep"] == 0 after reset
- env.timestep == 0 after reset
- obs_a["obstacles"] is a list
- obs_a["agent_b_velocity"] is a tuple of 2 floats
- generate_observations() key set is identical on repeated calls
- obs_b is always {} from generate_observations()
- state_dict() contains agent_b, target, timestep keys
- state_dict() positions match obs_a positions
- reset() with same seed produces same obs_a positions
- reset() with different seed may produce different positions
- step() message validation and latency buffer wiring
- step() timestep increments
- step() reward and termination for non-capture steps
- step() info["message"] contains delayed message
"""

import json
import tempfile
import os

import pytest

from env.environment import DecPOMDPEnvironment
from env.errors import EpisodeTerminatedError, MessageDimensionError

# ---------------------------------------------------------------------------
# Minimal valid config factory
# ---------------------------------------------------------------------------

_BASE_CONFIG = {
    "world_width": 400.0,
    "world_height": 300.0,
    "agent_radius": 10.0,
    "max_speed": 100.0,
    "max_angular_velocity": 0.3,
    "capture_radius": 15.0,
    "random_seed": 42,
    "max_steps": 200,
    "tau": 2,
    "min_separation": 50.0,
    "obstacles": [
        {"type": "rect", "cx": 200.0, "cy": 150.0, "width": 30.0, "height": 20.0, "angle": 0.0},
        {"type": "circle", "cx": 100.0, "cy": 100.0, "radius": 15.0},
    ],
    "render": False,
    "log_level": "WARNING",
}

_OBS_A_REQUIRED_KEYS = {"agent_a", "agent_b", "agent_b_velocity", "target", "obstacles", "timestep"}


def _write_config(cfg: dict) -> str:
    """Write config dict to a temp file and return the path."""
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(cfg, f)
    return path


@pytest.fixture
def config_path():
    path = _write_config(_BASE_CONFIG)
    yield path
    os.unlink(path)


@pytest.fixture
def env(config_path):
    return DecPOMDPEnvironment(config_path)


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------

def test_init_loads_config_without_error(config_path):
    """__init__ should succeed with a valid config file."""
    env = DecPOMDPEnvironment(config_path)
    assert env is not None


# ---------------------------------------------------------------------------
# reset() return type
# ---------------------------------------------------------------------------

def test_reset_returns_two_tuple(env):
    result = env.reset()
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_reset_obs_a_is_dict(env):
    obs_a, _ = env.reset()
    assert isinstance(obs_a, dict)


def test_reset_obs_b_is_empty_dict(env):
    _, obs_b = env.reset()
    assert obs_b == {}


# ---------------------------------------------------------------------------
# obs_a required keys
# ---------------------------------------------------------------------------

def test_reset_obs_a_has_all_required_keys(env):
    obs_a, _ = env.reset()
    assert _OBS_A_REQUIRED_KEYS == set(obs_a.keys())


def test_reset_obs_a_timestep_is_zero(env):
    obs_a, _ = env.reset()
    assert obs_a["timestep"] == 0


def test_reset_env_timestep_is_zero(env):
    env.reset()
    assert env.timestep == 0


def test_reset_obs_a_obstacles_is_list(env):
    obs_a, _ = env.reset()
    assert isinstance(obs_a["obstacles"], list)


def test_reset_obs_a_agent_b_velocity_is_tuple_of_two_floats(env):
    obs_a, _ = env.reset()
    vel = obs_a["agent_b_velocity"]
    assert isinstance(vel, tuple)
    assert len(vel) == 2
    assert isinstance(vel[0], float)
    assert isinstance(vel[1], float)


def test_reset_obs_a_agent_a_is_tuple_of_two_floats(env):
    obs_a, _ = env.reset()
    pos = obs_a["agent_a"]
    assert isinstance(pos, tuple) and len(pos) == 2


def test_reset_obs_a_agent_b_is_tuple_of_two_floats(env):
    obs_a, _ = env.reset()
    pos = obs_a["agent_b"]
    assert isinstance(pos, tuple) and len(pos) == 2


def test_reset_obs_a_target_is_tuple_of_two_floats(env):
    obs_a, _ = env.reset()
    pos = obs_a["target"]
    assert isinstance(pos, tuple) and len(pos) == 2


# ---------------------------------------------------------------------------
# generate_observations() consistency
# ---------------------------------------------------------------------------

def test_generate_observations_key_set_identical_on_repeated_calls(env):
    env.reset()
    obs_a1, _ = env.generate_observations()
    obs_a2, _ = env.generate_observations()
    assert set(obs_a1.keys()) == set(obs_a2.keys())


def test_generate_observations_obs_b_always_empty(env):
    env.reset()
    for _ in range(3):
        _, obs_b = env.generate_observations()
        assert obs_b == {}


# ---------------------------------------------------------------------------
# state_dict()
# ---------------------------------------------------------------------------

def test_state_dict_contains_required_keys(env):
    env.reset()
    sd = env.state_dict()
    assert "agent_b" in sd
    assert "target" in sd
    assert "timestep" in sd


def test_state_dict_contains_agent_b_velocity(env):
    env.reset()
    sd = env.state_dict()
    assert "agent_b_velocity" in sd


def test_state_dict_positions_match_obs_a(env):
    obs_a, _ = env.reset()
    sd = env.state_dict()
    assert sd["agent_b"] == obs_a["agent_b"]
    assert sd["target"] == obs_a["target"]


def test_state_dict_timestep_matches_env_timestep(env):
    env.reset()
    sd = env.state_dict()
    assert sd["timestep"] == env.timestep


# ---------------------------------------------------------------------------
# Seed reproducibility
# ---------------------------------------------------------------------------

def test_reset_same_seed_produces_same_positions(config_path):
    env1 = DecPOMDPEnvironment(config_path)
    env2 = DecPOMDPEnvironment(config_path)
    obs_a1, _ = env1.reset(seed=7)
    obs_a2, _ = env2.reset(seed=7)
    assert obs_a1["agent_b"] == obs_a2["agent_b"]
    assert obs_a1["agent_a"] == obs_a2["agent_a"]
    assert obs_a1["target"] == obs_a2["target"]


def test_reset_different_seeds_may_produce_different_positions(config_path):
    """Different seeds should (with overwhelming probability) produce different layouts."""
    env = DecPOMDPEnvironment(config_path)
    obs_a1, _ = env.reset(seed=1)
    obs_a2, _ = env.reset(seed=999999)
    # It is astronomically unlikely that two different seeds produce identical positions
    assert obs_a1["agent_b"] != obs_a2["agent_b"] or obs_a1["target"] != obs_a2["target"]


# ---------------------------------------------------------------------------
# Obstacles geometry in obs_a
# ---------------------------------------------------------------------------

def test_reset_obs_a_obstacles_have_type_key(env):
    obs_a, _ = env.reset()
    for obs_dict in obs_a["obstacles"]:
        assert "type" in obs_dict


def test_reset_obs_a_obstacles_count_matches_config():
    cfg = dict(_BASE_CONFIG)
    path = _write_config(cfg)
    try:
        env = DecPOMDPEnvironment(path)
        obs_a, _ = env.reset()
        assert len(obs_a["obstacles"]) == len(cfg["obstacles"])
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# step() — message validation (Requirements 9.1, 9.2)
# ---------------------------------------------------------------------------

def test_step_valid_16_float_message_accepted(env):
    """A valid 16-float message should not raise any error."""
    env.reset()
    result = env.step((0.0, 0.0), [0.0] * 16)
    assert result is not None


def test_step_message_length_0_raises_dimension_error(env):
    env.reset()
    with pytest.raises(MessageDimensionError):
        env.step((0.0, 0.0), [])


def test_step_message_length_15_raises_dimension_error(env):
    env.reset()
    with pytest.raises(MessageDimensionError):
        env.step((0.0, 0.0), [0.0] * 15)


def test_step_message_length_17_raises_dimension_error(env):
    env.reset()
    with pytest.raises(MessageDimensionError):
        env.step((0.0, 0.0), [0.0] * 17)


def test_step_message_length_32_raises_dimension_error(env):
    env.reset()
    with pytest.raises(MessageDimensionError):
        env.step((0.0, 0.0), [0.0] * 32)


def test_step_dimension_error_message_contains_actual_length(env):
    """MessageDimensionError message should contain the actual length received."""
    env.reset()
    with pytest.raises(MessageDimensionError) as exc_info:
        env.step((0.0, 0.0), [0.0] * 7)
    assert "7" in str(exc_info.value)


# ---------------------------------------------------------------------------
# step() — timestep increments (Requirement 12.3)
# ---------------------------------------------------------------------------

def test_step_increments_timestep_by_one(env):
    env.reset()
    assert env.timestep == 0
    env.step((0.0, 0.0), [0.0] * 16)
    assert env.timestep == 1


def test_step_n_times_timestep_equals_n(env):
    env.reset()
    n = 5
    for _ in range(n):
        env.step((0.0, 0.0), [0.0] * 16)
    assert env.timestep == n


# ---------------------------------------------------------------------------
# step() — terminated episode raises error (Requirements 11.5, 12.2)
# ---------------------------------------------------------------------------

def test_step_on_terminated_episode_raises_error(config_path):
    """step() on a terminated episode should raise EpisodeTerminatedError."""
    # Use a config with max_steps=1 so it terminates quickly
    cfg = dict(_BASE_CONFIG)
    cfg["max_steps"] = 1
    path = _write_config(cfg)
    try:
        e = DecPOMDPEnvironment(path)
        e.reset()
        e.step((0.0, 0.0), [0.0] * 16)  # reaches max_steps, terminates
        with pytest.raises(EpisodeTerminatedError):
            e.step((0.0, 0.0), [0.0] * 16)
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# step() — info["message"] latency buffer (Requirements 10.1–10.4)
# ---------------------------------------------------------------------------

def test_step_info_message_is_list_of_16_floats(env):
    """info['message'] should be a list of 16 floats."""
    env.reset()
    result = env.step((0.0, 0.0), [0.0] * 16)
    msg = result.info["message"]
    assert isinstance(msg, list)
    assert len(msg) == 16


def test_step_early_steps_return_zero_vector_in_info_message():
    """Before the buffer fills (tau steps), info['message'] should be zero vector."""
    cfg = dict(_BASE_CONFIG)
    cfg["tau"] = 3  # buffer fills after 3 pushes
    path = _write_config(cfg)
    try:
        e = DecPOMDPEnvironment(path)
        e.reset()
        sent = [1.0] * 16
        # First tau steps: buffer not yet full, should return zero vector
        for _ in range(3):
            result = e.step((0.0, 0.0), sent)
            assert result.info["message"] == [0.0] * 16
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# step() — reward and termination for non-capture steps (Requirements 11.3, 11.4)
# ---------------------------------------------------------------------------

def test_step_reward_is_zero_for_non_capture_step(env):
    env.reset()
    result = env.step((0.0, 0.0), [0.0] * 16)
    assert result.reward == 0.0


def test_step_terminated_is_false_for_non_capture_step(env):
    env.reset()
    result = env.step((0.0, 0.0), [0.0] * 16)
    assert result.terminated is False


# ---------------------------------------------------------------------------
# step() — Agent B position changes with non-zero speed action
# ---------------------------------------------------------------------------

def test_step_agent_b_position_changes_with_nonzero_speed(env):
    """Agent B should move when given a non-zero speed action."""
    env.reset()
    initial_pos = (env._agent_b.x, env._agent_b.y)
    # Apply a large speed boost
    env.step((0.0, 50.0), [0.0] * 16)
    new_pos = (env._agent_b.x, env._agent_b.y)
    assert initial_pos != new_pos


# ---------------------------------------------------------------------------
# step() — obs_b is always {} (Requirement 8.2)
# ---------------------------------------------------------------------------

def test_step_obs_b_is_always_empty(env):
    env.reset()
    result = env.step((0.0, 0.0), [0.0] * 16)
    assert result.obs_b == {}


# ---------------------------------------------------------------------------
# step() — obs_a["timestep"] matches env.timestep after step (Requirement 8.6)
# ---------------------------------------------------------------------------

def test_step_obs_a_timestep_matches_env_timestep(env):
    env.reset()
    result = env.step((0.0, 0.0), [0.0] * 16)
    assert result.obs_a["timestep"] == env.timestep


# ---------------------------------------------------------------------------
# No-obstacle config
# ---------------------------------------------------------------------------

def test_reset_with_no_obstacles():
    cfg = dict(_BASE_CONFIG)
    cfg["obstacles"] = []
    path = _write_config(cfg)
    try:
        env = DecPOMDPEnvironment(path)
        obs_a, obs_b = env.reset()
        assert obs_a["obstacles"] == []
        assert obs_b == {}
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Task 12: Reset mechanism tests (Requirements 13.1, 13.2, 13.3, 13.4)
# ---------------------------------------------------------------------------

def test_reset_after_mid_episode_returns_timestep_zero(env):
    """reset() after mid-episode steps should return timestep == 0."""
    env.reset()
    for _ in range(5):
        env.step((0.0, 0.0), [0.0] * 16)
    assert env.timestep == 5
    obs_a, _ = env.reset()
    assert env.timestep == 0
    assert obs_a["timestep"] == 0


def test_reset_after_terminated_episode_returns_timestep_zero(config_path):
    """reset() after a terminated episode should return timestep == 0."""
    cfg = dict(_BASE_CONFIG)
    cfg["max_steps"] = 3
    path = _write_config(cfg)
    try:
        e = DecPOMDPEnvironment(path)
        e.reset()
        for _ in range(3):
            e.step((0.0, 0.0), [0.0] * 16)
        assert e._terminated is True
        obs_a, _ = e.reset()
        assert e.timestep == 0
        assert obs_a["timestep"] == 0
    finally:
        os.unlink(path)


def test_reset_clears_latency_buffer(config_path):
    """reset() clears the latency buffer — first pop after reset returns zero vector."""
    cfg = dict(_BASE_CONFIG)
    cfg["tau"] = 2
    path = _write_config(cfg)
    try:
        e = DecPOMDPEnvironment(path)
        e.reset()
        # Push some messages to partially fill the buffer
        non_zero = [1.0] * 16
        e.step((0.0, 0.0), non_zero)
        e.step((0.0, 0.0), non_zero)
        # Now reset — buffer should be cleared
        e.reset()
        # After reset, the first pop should return zero vector (buffer is empty)
        result = e.step((0.0, 0.0), [0.0] * 16)
        assert result.info["message"] == [0.0] * 16
    finally:
        os.unlink(path)


def test_reset_with_new_seed_produces_different_layout(config_path):
    """reset() with a new seed should produce a different layout than the previous seed."""
    env = DecPOMDPEnvironment(config_path)
    obs_a1, _ = env.reset(seed=1)
    obs_a2, _ = env.reset(seed=999999)
    # Astronomically unlikely that two different seeds produce identical positions
    assert (
        obs_a1["agent_b"] != obs_a2["agent_b"]
        or obs_a1["target"] != obs_a2["target"]
    )


def test_reset_returns_obs_a_obs_b_tuple_with_correct_types(env):
    """reset() returns (obs_a, obs_b) tuple where obs_a is dict and obs_b is dict."""
    result = env.reset()
    assert isinstance(result, tuple)
    assert len(result) == 2
    obs_a, obs_b = result
    assert isinstance(obs_a, dict)
    assert isinstance(obs_b, dict)
    # obs_a must have all required keys
    assert _OBS_A_REQUIRED_KEYS == set(obs_a.keys())
    # obs_b must be empty
    assert obs_b == {}


def test_double_reset_works_correctly(env):
    """reset() after reset() should work correctly and return timestep == 0."""
    env.reset()
    env.step((0.0, 0.0), [0.0] * 16)
    obs_a1, _ = env.reset()
    obs_a2, _ = env.reset()
    assert env.timestep == 0
    assert obs_a2["timestep"] == 0
    # Both resets should return valid observations
    assert _OBS_A_REQUIRED_KEYS == set(obs_a1.keys())
    assert _OBS_A_REQUIRED_KEYS == set(obs_a2.keys())


# ---------------------------------------------------------------------------
# Task 14: Logging, extensibility, and close() tests
# (Requirements 15.1, 15.3, 16.1, 16.2, 16.3, 16.4)
# ---------------------------------------------------------------------------

def test_custom_generator_injection(config_path):
    """Custom ProceduralGenerator injection should work correctly."""
    from env.procedural_gen import ProceduralGenerator

    class FixedGenerator(ProceduralGenerator):
        """Generator that always places entities at fixed positions."""
        def generate(self, seed: int):
            from env.procedural_gen import GeneratedLayout
            from env.objects import AgentA, AgentB, Target
            return GeneratedLayout(
                agent_a=AgentA(id="agent_a", x=50.0, y=50.0),
                agent_b=AgentB(id="agent_b", x=100.0, y=100.0),
                target=Target(id="target", x=300.0, y=200.0),
                obstacles=[],
            )

    from env.config_loader import ConfigLoader
    config = ConfigLoader.load(config_path)
    custom_gen = FixedGenerator(config)

    env = DecPOMDPEnvironment(config_path, generator=custom_gen)
    obs_a, obs_b = env.reset()

    # Positions should match what the custom generator returns
    assert obs_a["agent_b"] == (100.0, 100.0)
    assert obs_a["target"] == (300.0, 200.0)
    assert obs_a["agent_a"] == (50.0, 50.0)


def test_environment_runs_with_warning_log_level():
    """Environment should run fully with log_level='WARNING' without errors."""
    cfg = dict(_BASE_CONFIG)
    cfg["log_level"] = "WARNING"
    path = _write_config(cfg)
    try:
        env = DecPOMDPEnvironment(path)
        obs_a, obs_b = env.reset()
        assert obs_a is not None
        result = env.step((0.0, 10.0), [0.0] * 16)
        assert result is not None
        assert result.reward == 0.0 or result.reward == 1.0
    finally:
        os.unlink(path)


def test_close_method_exists_and_can_be_called_safely(env):
    """close() method should exist and be callable without error."""
    env.reset()
    assert hasattr(env, "close")
    # Should not raise even when renderer is None
    env.close()
    # Can be called again safely
    env.close()


def test_close_sets_renderer_to_none(env):
    """close() should set _renderer to None."""
    env.reset()
    env.close()
    assert env._renderer is None


def test_environment_accepts_generator_parameter(config_path):
    """DecPOMDPEnvironment.__init__ should accept a generator keyword argument."""
    import inspect
    sig = inspect.signature(DecPOMDPEnvironment.__init__)
    assert "generator" in sig.parameters


def test_state_dict_agent_b_velocity_matches_entity(env):
    """state_dict() agent_b_velocity should match _agent_b.vx, _agent_b.vy."""
    env.reset()
    env.step((0.1, 30.0), [0.0] * 16)
    sd = env.state_dict()
    assert sd["agent_b_velocity"] == (env._agent_b.vx, env._agent_b.vy)


def test_state_dict_agent_b_position_matches_entity(env):
    """state_dict() agent_b position should match _agent_b.x, _agent_b.y."""
    env.reset()
    env.step((0.0, 20.0), [0.0] * 16)
    sd = env.state_dict()
    assert sd["agent_b"] == (env._agent_b.x, env._agent_b.y)
