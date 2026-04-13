"""Configuration loader for the Dec-POMDP environment."""

import json
from dataclasses import dataclass

from env.errors import ConfigValidationError

REQUIRED_FIELDS: list[str] = [
    "grid_width",
    "grid_height",
    "num_obstacles",
    "random_seed",
    "max_steps",
    "tau",
]

FIELD_TYPES: dict[str, type] = {
    "grid_width": int,
    "grid_height": int,
    "num_obstacles": int,
    "random_seed": int,
    "max_steps": int,
    "tau": int,
    "min_separation": int,
    "message_dim": int,
    "debug": bool,
    "log_level": str,
}


@dataclass
class EnvConfig:
    grid_width: int
    grid_height: int
    num_obstacles: int
    random_seed: int
    max_steps: int
    tau: int
    min_separation: int = 0
    message_dim: int = 16
    debug: bool = False
    log_level: str = "INFO"


class ConfigLoader:
    @staticmethod
    def load(path: str) -> EnvConfig:
        """Load and validate a JSON config file.

        Args:
            path: Path to the JSON config file.

        Returns:
            A validated EnvConfig dataclass instance.

        Raises:
            FileNotFoundError: If the file does not exist.
            ConfigValidationError: If a required field is missing or has the wrong type.
        """
        with open(path, "r") as f:
            data: dict = json.load(f)

        # Validate required fields
        for field in REQUIRED_FIELDS:
            if field not in data:
                raise ConfigValidationError(
                    f"Missing required config field: '{field}'"
                )
            expected_type = FIELD_TYPES[field]
            # bool is a subclass of int in Python; guard against accepting True/False for int fields
            value = data[field]
            if isinstance(value, bool) and expected_type is int:
                raise ConfigValidationError(
                    f"Config field '{field}' has wrong type: expected int, got bool"
                )
            if not isinstance(value, expected_type):
                raise ConfigValidationError(
                    f"Config field '{field}' has wrong type: "
                    f"expected {expected_type.__name__}, got {type(value).__name__}"
                )

        # Validate optional fields if present
        optional_fields = ["min_separation", "message_dim", "debug", "log_level"]
        for field in optional_fields:
            if field in data:
                expected_type = FIELD_TYPES[field]
                value = data[field]
                if isinstance(value, bool) and expected_type is int:
                    raise ConfigValidationError(
                        f"Config field '{field}' has wrong type: expected int, got bool"
                    )
                if not isinstance(value, expected_type):
                    raise ConfigValidationError(
                        f"Config field '{field}' has wrong type: "
                        f"expected {expected_type.__name__}, got {type(value).__name__}"
                    )

        return EnvConfig(
            grid_width=data["grid_width"],
            grid_height=data["grid_height"],
            num_obstacles=data["num_obstacles"],
            random_seed=data["random_seed"],
            max_steps=data["max_steps"],
            tau=data["tau"],
            min_separation=data.get("min_separation", 0),
            message_dim=data.get("message_dim", 16),
            debug=data.get("debug", False),
            log_level=data.get("log_level", "INFO"),
        )
