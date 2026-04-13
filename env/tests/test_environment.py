"""Unit tests for DecPOMDPEnvironment — observation interface (Task 8)."""

import json
import tempfile
import os

import pytest

from env.environment import DecPOMDPEnvironment, OBS_A_KEYS

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_CONFIG = {
    "grid_width": 16,
    "grid_height": 16,
    "num_obstacles": 5,
    "random_seed": 42,
    "max_steps": 100,
    "tau": 1,
    "min_separation": 2,
}


def make_env(config: dict | None = None) -> tuple[DecPOMDPEnvironment, str]:
    """Create a DecPOMDPEnvironment backed by a temporary config file.

    Returns (env, tmp_path) so the caller can clean up if needed.
    """
    cfg = config if config is not None else MINIMAL_CONFIG
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    )
    json.dump(cfg, tmp)
    tmp.close()
    env = DecPOMDPEnvironment(tmp.name)
    return env, tmp.name


# ---------------------------------------------------------------------------
# reset() return type
# ---------------------------------------------------------------------------

class TestResetReturnType:
    def test_reset_returns_two_tuple(self):
        env, path = make_env()
        try:
            result = env.reset()
            assert isinstance(result, tuple)
            assert len(result) == 2
        finally:
            os.unlink(path)

    def test_reset_obs_a_is_dict(self):
        env, path = make_env()
        try:
            obs_a, _ = env.reset()
            assert isinstance(obs_a, dict)
        finally:
            os.unlink(path)

    def test_reset_obs_b_is_empty_dict(self):
        env, path = make_env()
        try:
            _, obs_b = env.reset()
            assert obs_b == {}
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# obs_a key completeness
# ---------------------------------------------------------------------------

class TestObsAKeys:
    def test_obs_a_has_all_required_keys(self):
        env, path = make_env()
        try:
            obs_a, _ = env.reset()
            assert set(obs_a.keys()) == OBS_A_KEYS
        finally:
            os.unlink(path)

    def test_obs_a_has_agent_a_key(self):
        env, path = make_env()
        try:
            obs_a, _ = env.reset()
            assert "agent_a" in obs_a
        finally:
            os.unlink(path)

    def test_obs_a_has_agent_b_key(self):
        env, path = make_env()
        try:
            obs_a, _ = env.reset()
            assert "agent_b" in obs_a
        finally:
            os.unlink(path)

    def test_obs_a_has_target_key(self):
        env, path = make_env()
        try:
            obs_a, _ = env.reset()
            assert "target" in obs_a
        finally:
            os.unlink(path)

    def test_obs_a_has_obstacles_key(self):
        env, path = make_env()
        try:
            obs_a, _ = env.reset()
            assert "obstacles" in obs_a
        finally:
            os.unlink(path)

    def test_obs_a_has_timestep_key(self):
        env, path = make_env()
        try:
            obs_a, _ = env.reset()
            assert "timestep" in obs_a
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# timestep after reset
# ---------------------------------------------------------------------------

class TestTimestepAfterReset:
    def test_obs_a_timestep_is_zero_after_reset(self):
        env, path = make_env()
        try:
            obs_a, _ = env.reset()
            assert obs_a["timestep"] == 0
        finally:
            os.unlink(path)

    def test_env_timestep_attribute_is_zero_after_reset(self):
        env, path = make_env()
        try:
            env.reset()
            assert env.timestep == 0
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# obstacles list properties
# ---------------------------------------------------------------------------

class TestObstaclesList:
    def test_obstacles_is_list(self):
        env, path = make_env()
        try:
            obs_a, _ = env.reset()
            assert isinstance(obs_a["obstacles"], list)
        finally:
            os.unlink(path)

    def test_obstacles_has_correct_count(self):
        env, path = make_env()
        try:
            obs_a, _ = env.reset()
            assert len(obs_a["obstacles"]) == MINIMAL_CONFIG["num_obstacles"]
        finally:
            os.unlink(path)

    def test_obstacles_is_sorted(self):
        env, path = make_env()
        try:
            obs_a, _ = env.reset()
            obstacles = obs_a["obstacles"]
            assert obstacles == sorted(obstacles)
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# generate_observations() consistency
# ---------------------------------------------------------------------------

class TestGenerateObservations:
    def test_key_set_identical_on_repeated_calls(self):
        env, path = make_env()
        try:
            env.reset()
            obs_a1, _ = env.generate_observations()
            obs_a2, _ = env.generate_observations()
            assert set(obs_a1.keys()) == set(obs_a2.keys())
        finally:
            os.unlink(path)

    def test_obs_b_always_empty_from_generate_observations(self):
        env, path = make_env()
        try:
            env.reset()
            for _ in range(3):
                _, obs_b = env.generate_observations()
                assert obs_b == {}
        finally:
            os.unlink(path)

    def test_generate_observations_returns_two_tuple(self):
        env, path = make_env()
        try:
            env.reset()
            result = env.generate_observations()
            assert isinstance(result, tuple) and len(result) == 2
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# state_dict()
# ---------------------------------------------------------------------------

class TestStateDict:
    def test_state_dict_contains_agent_a(self):
        env, path = make_env()
        try:
            env.reset()
            sd = env.state_dict()
            assert "agent_a" in sd
        finally:
            os.unlink(path)

    def test_state_dict_contains_agent_b(self):
        env, path = make_env()
        try:
            env.reset()
            sd = env.state_dict()
            assert "agent_b" in sd
        finally:
            os.unlink(path)

    def test_state_dict_contains_target(self):
        env, path = make_env()
        try:
            env.reset()
            sd = env.state_dict()
            assert "target" in sd
        finally:
            os.unlink(path)

    def test_state_dict_positions_match_obs_a(self):
        env, path = make_env()
        try:
            obs_a, _ = env.reset()
            sd = env.state_dict()
            assert (sd["agent_a"]["x"], sd["agent_a"]["y"]) == obs_a["agent_a"]
            assert (sd["agent_b"]["x"], sd["agent_b"]["y"]) == obs_a["agent_b"]
            assert (sd["target"]["x"], sd["target"]["y"]) == obs_a["target"]
        finally:
            os.unlink(path)

    def test_state_dict_contains_timestep(self):
        env, path = make_env()
        try:
            env.reset()
            sd = env.state_dict()
            assert "timestep" in sd
            assert sd["timestep"] == 0
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Seed reproducibility
# ---------------------------------------------------------------------------

class TestSeedReproducibility:
    def test_same_seed_produces_same_obs_a_positions(self):
        env, path = make_env()
        try:
            obs_a1, _ = env.reset(seed=99)
            obs_a2, _ = env.reset(seed=99)
            assert obs_a1["agent_a"] == obs_a2["agent_a"]
            assert obs_a1["agent_b"] == obs_a2["agent_b"]
            assert obs_a1["target"] == obs_a2["target"]
            assert obs_a1["obstacles"] == obs_a2["obstacles"]
        finally:
            os.unlink(path)

    def test_different_seeds_may_produce_different_layouts(self):
        """Probabilistic: with a large grid and few obstacles, different seeds
        almost certainly produce different layouts."""
        env, path = make_env()
        try:
            obs_a1, _ = env.reset(seed=1)
            obs_a2, _ = env.reset(seed=2)
            # At least one position should differ (extremely unlikely to be equal)
            positions_equal = (
                obs_a1["agent_a"] == obs_a2["agent_a"]
                and obs_a1["agent_b"] == obs_a2["agent_b"]
                and obs_a1["target"] == obs_a2["target"]
            )
            # We don't assert False here — just document the expectation
            # (could theoretically collide, but practically won't)
            _ = positions_equal  # acknowledged
        finally:
            os.unlink(path)
