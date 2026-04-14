"""Config loader: parse and validate JSON config for the Dec-POMDP environment."""

import json
from dataclasses import dataclass, field
from typing import Any

from env.errors import ConfigValidationError, InvalidObstacleError


# ---------------------------------------------------------------------------
# EnvConfig dataclass
# ---------------------------------------------------------------------------

@dataclass
class EnvConfig:
    # World (required)
    world_width: float
    world_height: float
    # Physics (required)
    agent_radius: float
    max_speed: float
    max_angular_velocity: float
    capture_radius: float
    # Episode (required)
    random_seed: int
    max_steps: int
    tau: int
    # Optional with defaults
    min_separation: float = 0.0
    obstacles: list = field(default_factory=list)
    procedural: dict | None = None
    render: bool = False
    log_level: str = "INFO"
    message_dim: int = 16


# ---------------------------------------------------------------------------
# Field specifications
# ---------------------------------------------------------------------------

# Required fields and their expected Python types
_REQUIRED_FLOAT_FIELDS = (
    "world_width",
    "world_height",
    "agent_radius",
    "max_speed",
    "max_angular_velocity",
    "capture_radius",
)

_REQUIRED_INT_FIELDS = (
    "random_seed",
    "max_steps",
    "tau",
)

REQUIRED_FIELDS = _REQUIRED_FLOAT_FIELDS + _REQUIRED_INT_FIELDS


# ---------------------------------------------------------------------------
# Obstacle validation helpers
# ---------------------------------------------------------------------------

def _validate_obstacle(obs: Any, index: int) -> None:
    """Validate a single obstacle dict. Raises InvalidObstacleError on failure."""
    if not isinstance(obs, dict):
        raise InvalidObstacleError(
            f"obstacles[{index}]: expected a dict, got {type(obs).__name__}"
        )

    obs_type = obs.get("type")
    if obs_type is None:
        raise InvalidObstacleError(
            f"obstacles[{index}]: missing required field 'type'"
        )

    if obs_type == "rect":
        _validate_rect(obs, index)
    elif obs_type == "circle":
        _validate_circle(obs, index)
    elif obs_type == "polygon":
        _validate_polygon(obs, index)
    else:
        raise InvalidObstacleError(
            f"obstacles[{index}]: unknown obstacle type '{obs_type}'"
        )


def _require_float(obs: dict, key: str, index: int, label: str) -> float:
    """Extract a float field from an obstacle dict, raising InvalidObstacleError if missing/wrong type."""
    if key not in obs:
        raise InvalidObstacleError(
            f"obstacles[{index}] ({label}): missing required field '{key}'"
        )
    val = obs[key]
    if not isinstance(val, (int, float)):
        raise InvalidObstacleError(
            f"obstacles[{index}] ({label}): field '{key}' must be a number, got {type(val).__name__}"
        )
    return float(val)


def _validate_rect(obs: dict, index: int) -> None:
    _require_float(obs, "cx", index, "rect")
    _require_float(obs, "cy", index, "rect")
    width = _require_float(obs, "width", index, "rect")
    height = _require_float(obs, "height", index, "rect")
    _require_float(obs, "angle", index, "rect")
    if width <= 0:
        raise InvalidObstacleError(
            f"obstacles[{index}] (rect): 'width' must be > 0, got {width}"
        )
    if height <= 0:
        raise InvalidObstacleError(
            f"obstacles[{index}] (rect): 'height' must be > 0, got {height}"
        )


def _validate_circle(obs: dict, index: int) -> None:
    _require_float(obs, "cx", index, "circle")
    _require_float(obs, "cy", index, "circle")
    radius = _require_float(obs, "radius", index, "circle")
    if radius <= 0:
        raise InvalidObstacleError(
            f"obstacles[{index}] (circle): 'radius' must be > 0, got {radius}"
        )


def _validate_polygon(obs: dict, index: int) -> None:
    if "vertices" not in obs:
        raise InvalidObstacleError(
            f"obstacles[{index}] (polygon): missing required field 'vertices'"
        )
    vertices = obs["vertices"]
    if not isinstance(vertices, list):
        raise InvalidObstacleError(
            f"obstacles[{index}] (polygon): 'vertices' must be a list"
        )
    if len(vertices) < 3:
        raise InvalidObstacleError(
            f"obstacles[{index}] (polygon): 'vertices' must have at least 3 points, "
            f"got {len(vertices)}"
        )
    for vi, v in enumerate(vertices):
        if (
            not isinstance(v, (list, tuple))
            or len(v) != 2
            or not all(isinstance(c, (int, float)) for c in v)
        ):
            raise InvalidObstacleError(
                f"obstacles[{index}] (polygon): vertex {vi} must be a [float, float] pair"
            )


# ---------------------------------------------------------------------------
# ConfigLoader
# ---------------------------------------------------------------------------

class ConfigLoader:
    @staticmethod
    def load(path: str) -> EnvConfig:
        """Read and validate a JSON config file.

        Raises:
            FileNotFoundError: if the file does not exist.
            ConfigValidationError: if a required field is missing or has the wrong type
                (message contains the offending field name).
            InvalidObstacleError: if an obstacle definition is invalid.
        """
        with open(path, "r") as f:
            data: dict = json.load(f)

        # Validate required float fields
        for field_name in _REQUIRED_FLOAT_FIELDS:
            if field_name not in data:
                raise ConfigValidationError(
                    f"Missing required config field: '{field_name}'"
                )
            val = data[field_name]
            if not isinstance(val, (int, float)):
                raise ConfigValidationError(
                    f"Config field '{field_name}' must be a number (float), "
                    f"got {type(val).__name__}"
                )

        # Validate required int fields
        for field_name in _REQUIRED_INT_FIELDS:
            if field_name not in data:
                raise ConfigValidationError(
                    f"Missing required config field: '{field_name}'"
                )
            val = data[field_name]
            if not isinstance(val, int) or isinstance(val, bool):
                raise ConfigValidationError(
                    f"Config field '{field_name}' must be an integer, "
                    f"got {type(val).__name__}"
                )

        # Validate obstacles list
        obstacles_raw = data.get("obstacles", [])
        if not isinstance(obstacles_raw, list):
            raise ConfigValidationError(
                "Config field 'obstacles' must be a list"
            )
        for i, obs in enumerate(obstacles_raw):
            _validate_obstacle(obs, i)

        return EnvConfig(
            world_width=float(data["world_width"]),
            world_height=float(data["world_height"]),
            agent_radius=float(data["agent_radius"]),
            max_speed=float(data["max_speed"]),
            max_angular_velocity=float(data["max_angular_velocity"]),
            capture_radius=float(data["capture_radius"]),
            random_seed=int(data["random_seed"]),
            max_steps=int(data["max_steps"]),
            tau=int(data["tau"]),
            min_separation=float(data.get("min_separation", 0.0)),
            obstacles=obstacles_raw,
            procedural=data.get("procedural", None),
            render=bool(data.get("render", False)),
            log_level=str(data.get("log_level", "INFO")),
            message_dim=int(data.get("message_dim", 16)),
        )
