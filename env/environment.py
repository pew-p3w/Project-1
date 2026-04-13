"""Dec-POMDP environment orchestrator."""

from __future__ import annotations

from collections import namedtuple
from typing import Optional

from env.config_loader import ConfigLoader, EnvConfig
from env.errors import EpisodeTerminatedError
from env.latency_buffer import LatencyBuffer
from env.objects import AgentA, AgentB, Obstacle, Target
from env.procedural_gen import ProceduralGenerator
from env.spatial import SpatialIndex

# Observation type aliases (for documentation purposes)
ObsA = dict
ObsB = dict

StepResult = namedtuple("StepResult", ["obs_a", "obs_b", "reward", "terminated", "info"])

# Required keys in Agent A's observation
OBS_A_KEYS = frozenset({"agent_a", "agent_b", "target", "obstacles", "timestep"})


class DecPOMDPEnvironment:
    """Asymmetric Dec-POMDP grid environment.

    Agent A (Observer) receives the full state; Agent B (Actor) receives nothing.
    Communication is mediated by a latency buffer with τ-step delay.

    Args:
        config_path: Path to the JSON configuration file.
    """

    def __init__(self, config_path: str) -> None:
        self._config: EnvConfig = ConfigLoader.load(config_path)
        self._generator: ProceduralGenerator = ProceduralGenerator(self._config)
        self._spatial_index: SpatialIndex = SpatialIndex()
        self._latency_buffer: LatencyBuffer = LatencyBuffer(
            tau=self._config.tau,
            message_dim=self._config.message_dim,
        )

        # Entity references — populated on reset()
        self._agent_a: Optional[AgentA] = None
        self._agent_b: Optional[AgentB] = None
        self._target: Optional[Target] = None
        self._obstacles: list[Obstacle] = []

        # Episode state
        self.timestep: int = 0
        self._terminated: bool = False
        self._current_seed: int = self._config.random_seed

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def reset(self, seed: Optional[int] = None) -> tuple[ObsA, ObsB]:
        """Clear state, run procedural generation, return initial observations.

        Args:
            seed: Optional seed override for this episode. If None, uses the
                  seed from config (or the last seed used).

        Returns:
            (obs_a, obs_b) — initial observations for both agents.
        """
        if seed is not None:
            self._current_seed = seed

        # Clear episode state
        self.timestep = 0
        self._terminated = False
        self._latency_buffer.clear()

        # Clear spatial index by rebuilding it
        self._spatial_index = SpatialIndex()
        self._agent_a = None
        self._agent_b = None
        self._target = None
        self._obstacles = []

        # Procedurally generate entities
        entities = self._generator.generate(self._current_seed)

        for entity in entities:
            if isinstance(entity, AgentA):
                self._agent_a = entity
            elif isinstance(entity, AgentB):
                self._agent_b = entity
            elif isinstance(entity, Target):
                self._target = entity
            elif isinstance(entity, Obstacle):
                self._obstacles.append(entity)
            self._spatial_index.add(entity)

        return self.generate_observations()

    def generate_observations(self) -> tuple[ObsA, ObsB]:
        """Generate observations for both agents from current state.

        Returns:
            (obs_a, obs_b) where obs_a contains full state and obs_b is {}.
        """
        assert self._agent_a is not None, "Environment not reset — call reset() first"
        assert self._agent_b is not None, "Environment not reset — call reset() first"
        assert self._target is not None, "Environment not reset — call reset() first"

        obs_a: ObsA = {
            "agent_a": (self._agent_a.x, self._agent_a.y),
            "agent_b": (self._agent_b.x, self._agent_b.y),
            "target": (self._target.x, self._target.y),
            "obstacles": sorted((obs.x, obs.y) for obs in self._obstacles),
            "timestep": self.timestep,
        }
        obs_b: ObsB = {}
        return obs_a, obs_b

    def state_dict(self) -> dict:
        """Return the full current state as a structured dictionary.

        Returns:
            Dict with positions of all entities and current timestep.
        """
        assert self._agent_a is not None, "Environment not reset — call reset() first"
        assert self._agent_b is not None, "Environment not reset — call reset() first"
        assert self._target is not None, "Environment not reset — call reset() first"

        return {
            "agent_a": {"x": self._agent_a.x, "y": self._agent_a.y},
            "agent_b": {"x": self._agent_b.x, "y": self._agent_b.y},
            "target": {"x": self._target.x, "y": self._target.y},
            "obstacles": [{"x": obs.x, "y": obs.y} for obs in self._obstacles],
            "timestep": self.timestep,
            "terminated": self._terminated,
        }

    def step(self, action_b: int, message_a: list[float]) -> StepResult:
        """Advance the environment by one timestep.

        Not yet implemented — will be wired in Tasks 9-12.

        Raises:
            NotImplementedError: Always, until Tasks 9-12 are complete.
        """
        raise NotImplementedError("step() will be implemented in Tasks 9-12")
