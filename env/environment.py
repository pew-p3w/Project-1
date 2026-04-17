"""Dec-POMDP Environment: orchestrates the step pipeline, reset, and episode lifecycle."""

from __future__ import annotations

import logging
import math
from collections import namedtuple
from typing import TypedDict

from env.config_loader import ConfigLoader, EnvConfig
from env.errors import EpisodeTerminatedError, MessageDimensionError
from env.latency_buffer import LatencyBuffer
from env.movement import apply_steering
from env.objects import (
    AgentA,
    AgentB,
    CircleDef,
    Obstacle,
    PolygonDef,
    RectDef,
    Target,
)
from env.physics_engine import PhysicsEngine
from env.procedural_gen import ProceduralGenerator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Named return types
# ---------------------------------------------------------------------------

StepResult = namedtuple("StepResult", ["obs_a", "obs_b", "reward", "terminated", "info"])


# ---------------------------------------------------------------------------
# Observation type aliases (for documentation purposes)
# ---------------------------------------------------------------------------

class ObsA(TypedDict):
    agent_a: tuple[float, float]
    agent_b: tuple[float, float]
    agent_b_velocity: tuple[float, float]
    target: tuple[float, float]
    obstacles: list[dict]
    timestep: int


# ObsB is always {}


# ---------------------------------------------------------------------------
# Helper: convert a shape_def to a plain dict
# ---------------------------------------------------------------------------

def _shape_def_to_dict(shape_def: RectDef | CircleDef | PolygonDef) -> dict:
    """Convert a shape definition dataclass to a plain dict matching the config schema."""
    if isinstance(shape_def, RectDef):
        return {
            "type": "rect",
            "cx": shape_def.cx,
            "cy": shape_def.cy,
            "width": shape_def.width,
            "height": shape_def.height,
            "angle": shape_def.angle,
        }
    elif isinstance(shape_def, CircleDef):
        return {
            "type": "circle",
            "cx": shape_def.cx,
            "cy": shape_def.cy,
            "radius": shape_def.radius,
        }
    elif isinstance(shape_def, PolygonDef):
        return {
            "type": "polygon",
            "vertices": [list(v) for v in shape_def.vertices],
        }
    else:
        raise TypeError(f"Unknown shape_def type: {type(shape_def)}")


# ---------------------------------------------------------------------------
# DecPOMDPEnvironment
# ---------------------------------------------------------------------------

class DecPOMDPEnvironment:
    """Orchestrates the Dec-POMDP episode lifecycle.

    Responsibilities:
    - Load and validate config at init time.
    - Reset: clear state, run procedural generation, register physics, return obs.
    - generate_observations: build ObsA and ObsB.
    - state_dict: expose full current state for debugging/logging.
    - step: (stub) raises NotImplementedError — implemented in Tasks 9-10.
    """

    def __init__(
        self,
        config_path: str,
        generator: ProceduralGenerator | None = None,
    ) -> None:
        self._config: EnvConfig = ConfigLoader.load(config_path)

        # Configure logging from config
        logging.basicConfig(level=getattr(logging, self._config.log_level, logging.INFO))

        self._physics: PhysicsEngine = PhysicsEngine(self._config)
        self._generator: ProceduralGenerator = (
            generator if generator is not None else ProceduralGenerator(self._config)
        )
        self._latency_buffer: LatencyBuffer = LatencyBuffer(
            tau=self._config.tau,
            message_dim=self._config.message_dim,
        )

        # Entity state — populated by reset()
        self._agent_a: AgentA | None = None
        self._agent_b: AgentB | None = None
        self._target: Target | None = None
        self._obstacles: list[Obstacle] = []

        # Episode state
        self.timestep: int = 0
        self._terminated: bool = False
        self._current_seed: int = self._config.random_seed
        self._last_reward: float = 0.0

        # Optional renderer (only imported when render=True)
        self._renderer = None
        if self._config.render:
            from env.renderer import Renderer
            self._renderer = Renderer(self._config)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self, seed: int | None = None) -> tuple[dict, dict]:
        """Clear all state, re-run procedural generation, return initial observations.

        Args:
            seed: Optional seed override. If None, uses config.random_seed.

        Returns:
            (obs_a, obs_b) tuple of initial observations. obs_a includes 'obstacles'.
        """
        self._current_seed = seed if seed is not None else self._config.random_seed

        # Reset subsystems
        self._physics.reset()
        self._latency_buffer.clear()
        self.timestep = 0
        self._terminated = False
        self._last_reward = 0.0

        # Generate layout
        layout = self._generator.generate(self._current_seed)
        self._agent_a = layout.agent_a
        self._agent_b = layout.agent_b
        self._target = layout.target
        self._obstacles = layout.obstacles

        # Register obstacles and agent_b with physics engine
        for obs in self._obstacles:
            if obs.shape_def is not None:
                self._physics.add_obstacle(obs.shape_def)
        self._physics.add_agent_b(
            self._agent_b.x,
            self._agent_b.y,
            self._config.agent_radius,
        )

        logger.debug(
            "reset(seed=%d): agent_a=(%.2f,%.2f) agent_b=(%.2f,%.2f) target=(%.2f,%.2f) "
            "obstacles=%d",
            self._current_seed,
            self._agent_a.x, self._agent_a.y,
            self._agent_b.x, self._agent_b.y,
            self._target.x, self._target.y,
            len(self._obstacles),
        )

        obs_a, obs_b = self.generate_observations()
        
        # Add obstacles only to the reset observation
        obstacle_dicts: list[dict] = []
        for obs in self._obstacles:
            if obs.shape_def is not None:
                obstacle_dicts.append(_shape_def_to_dict(obs.shape_def))
        obs_a["obstacles"] = obstacle_dicts

        return obs_a, obs_b

    def generate_observations(self) -> tuple[dict, dict]:
        """Build and return (obs_a, obs_b).

        obs_a contains the dynamic environment state.
        obs_b is always an empty dict.
        """
        assert self._agent_a is not None, "reset() must be called before generate_observations()"
        assert self._agent_b is not None
        assert self._target is not None

        obs_a: dict = {
            "agent_a": (self._agent_a.x, self._agent_a.y),
            "agent_b": (self._agent_b.x, self._agent_b.y),
            "agent_b_velocity": (self._agent_b.vx, self._agent_b.vy),
            "target": (self._target.x, self._target.y),
            "timestep": self.timestep,
        }
        obs_b: dict = {}

        return obs_a, obs_b

    def state_dict(self) -> dict:
        """Return full current state as a structured dictionary.

        Includes Agent A & B positions, Agent B velocity, Target position,
        Obstacle geometries, timestep, last reward, and terminated flag.
        """
        agent_a_pos = (self._agent_a.x, self._agent_a.y) if self._agent_a else None
        agent_b_pos = (self._agent_b.x, self._agent_b.y) if self._agent_b else None
        agent_b_vel = (self._agent_b.vx, self._agent_b.vy) if self._agent_b else None
        target_pos = (self._target.x, self._target.y) if self._target else None

        obstacle_dicts: list[dict] = []
        for obs in self._obstacles:
            if obs.shape_def is not None:
                obstacle_dicts.append(_shape_def_to_dict(obs.shape_def))

        return {
            "agent_a": agent_a_pos,
            "agent_b": agent_b_pos,
            "agent_b_velocity": agent_b_vel,
            "target": target_pos,
            "obstacles": obstacle_dicts,
            "timestep": self.timestep,
            "last_reward": self._last_reward,
            "terminated": self._terminated,
        }

    def step(
        self,
        action_b: tuple[float, float],
        message_a: list[float],
    ) -> StepResult:
        """Advance simulation by one timestep.

        Raises:
            EpisodeTerminatedError: if the episode is already terminated.
            MessageDimensionError: if len(message_a) != 16.
        """
        # 1. Validate episode is active
        if self._terminated:
            raise EpisodeTerminatedError(
                "Episode is terminated. Call reset() before stepping."
            )

        # 2. Validate message dimension
        if len(message_a) != 16:
            raise MessageDimensionError(
                f"message_a must have length 16, got {len(message_a)}"
            )

        # 3. Push message to latency buffer
        self._latency_buffer.push(message_a)

        # 4. Pop delayed message
        delayed_msg = self._latency_buffer.pop()

        # 5. Apply steering action to Agent B
        agent_b = self._agent_b
        config = self._config
        delta_heading, delta_speed = action_b
        new_heading, new_speed, new_vx, new_vy = apply_steering(
            agent_b.heading,
            agent_b.speed,
            delta_heading,
            delta_speed,
            config.max_angular_velocity,
            config.max_speed,
        )
        agent_b.heading = new_heading
        agent_b.speed = new_speed
        agent_b.vx = new_vx
        agent_b.vy = new_vy

        logger.debug(
            "step t=%d: action=(dh=%.4f, ds=%.4f) -> heading=%.4f speed=%.4f vx=%.4f vy=%.4f",
            self.timestep, delta_heading, delta_speed, new_heading, new_speed, new_vx, new_vy,
        )

        # 6. Apply velocity to physics engine
        self._physics.set_velocity(new_vx, new_vy)

        # 7. Advance physics
        self._physics.step()

        # 8. Query new position and velocity from physics
        x, y = self._physics.get_agent_b_position()
        agent_b.x = x
        agent_b.y = y
        vx, vy = self._physics.get_agent_b_velocity()
        agent_b.vx = vx
        agent_b.vy = vy

        logger.debug(
            "step t=%d: new position=(%.4f, %.4f) velocity=(%.4f, %.4f)",
            self.timestep, x, y, vx, vy,
        )

        # 9. Increment timestep
        self.timestep += 1

        # 10. Compute reward and termination
        reward, terminated = self._compute_reward_and_termination()

        # 11. Update episode state
        self._last_reward = reward
        self._terminated = terminated

        # 12. Render if renderer is active
        if self._renderer is not None:
            if not self._renderer.draw(self.state_dict()):
                self._terminated = True  # window closed

        # 13. Generate observations
        obs_a, obs_b = self.generate_observations()

        # 14. Return result
        return StepResult(obs_a, obs_b, reward, terminated, {"message": delayed_msg})

    def _compute_reward_and_termination(self) -> tuple[float, bool]:
        """Compute reward and termination flag based on current state."""
        agent_b = self._agent_b
        target = self._target
        dist = math.hypot(agent_b.x - target.x, agent_b.y - target.y)
        if dist <= self._config.capture_radius:
            logger.info(
                "Capture at t=%d! agent_b=(%.2f,%.2f) target=(%.2f,%.2f) dist=%.4f",
                self.timestep, agent_b.x, agent_b.y, target.x, target.y, dist,
            )
            return (1.0, True)
        if self.timestep >= self._config.max_steps:
            return (0.0, True)
        return (0.0, False)

    def close(self) -> None:
        """Close the renderer if open."""
        if self._renderer is not None:
            self._renderer.close()
            self._renderer = None
