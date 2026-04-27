"""Unit tests for env/config_loader.py."""

import json
import os
import tempfile

import pytest

from env.config_loader import ConfigLoader, EnvConfig, REQUIRED_FIELDS
from env.errors import ConfigValidationError, InvalidObstacleError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_CONFIG = {
    "world_width": 800.0,
    "world_height": 600.0,
    "agent_radius": 10.0,
    "max_speed": 150.0,
    "max_angular_velocity": 0.2,
    "capture_radius": 20.0,
    "random_seed": 42,
    "max_steps": 500,
    "tau": 3,
    "min_separation": 100.0,
    "obstacles": [],
    "render": False,
    "log_level": "INFO",
}


def _write_config(data: dict) -> str:
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
    return path


def _load(data: dict) -> EnvConfig:
    path = _write_config(data)
    try:
        return ConfigLoader.load(path)
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Valid config
# ---------------------------------------------------------------------------

class TestValidConfig:
    def test_loads_all_required_fields(self):
        cfg = _load(VALID_CONFIG)
        assert cfg.world_width == 800.0
        assert cfg.world_height == 600.0
        assert cfg.agent_radius == 10.0
        assert cfg.max_speed == 150.0
        assert cfg.max_angular_velocity == 0.2
        assert cfg.capture_radius == 20.0
        assert cfg.random_seed == 42
        assert cfg.max_steps == 500
        assert cfg.tau == 3

    def test_returns_env_config_instance(self):
        cfg = _load(VALID_CONFIG)
        assert isinstance(cfg, EnvConfig)


# ---------------------------------------------------------------------------
# Optional field defaults
# ---------------------------------------------------------------------------

class TestOptionalDefaults:
    def _minimal(self) -> dict:
        return {k: v for k, v in VALID_CONFIG.items() if k in REQUIRED_FIELDS}

    def test_min_separation_defaults_to_zero(self):
        cfg = _load(self._minimal())
        assert cfg.min_separation == 0.0

    def test_obstacles_defaults_to_empty_list(self):
        cfg = _load(self._minimal())
        assert cfg.obstacles == []

    def test_procedural_defaults_to_none(self):
        cfg = _load(self._minimal())
        assert cfg.procedural is None

    def test_render_defaults_to_false(self):
        cfg = _load(self._minimal())
        assert cfg.render is False

    def test_log_level_defaults_to_info(self):
        cfg = _load(self._minimal())
        assert cfg.log_level == "INFO"

    def test_message_dim_defaults_to_16(self):
        cfg = _load(self._minimal())
        assert cfg.message_dim == 16


# ---------------------------------------------------------------------------
# Missing required fields
# ---------------------------------------------------------------------------

class TestMissingRequiredFields:
    @pytest.mark.parametrize("field_name", REQUIRED_FIELDS)
    def test_missing_field_raises_config_validation_error(self, field_name):
        data = {k: v for k, v in VALID_CONFIG.items() if k != field_name}
        with pytest.raises(ConfigValidationError) as exc_info:
            _load(data)
        assert field_name in str(exc_info.value)

    @pytest.mark.parametrize("field_name", REQUIRED_FIELDS)
    def test_missing_field_error_names_field(self, field_name):
        data = {k: v for k, v in VALID_CONFIG.items() if k != field_name}
        with pytest.raises(ConfigValidationError) as exc_info:
            _load(data)
        assert field_name in str(exc_info.value), (
            f"Expected '{field_name}' in error message, got: {exc_info.value}"
        )


# ---------------------------------------------------------------------------
# Wrong type for required fields
# ---------------------------------------------------------------------------

class TestWrongTypeRequiredFields:
    @pytest.mark.parametrize("field_name", [
        "world_width", "world_height", "agent_radius",
        "max_speed", "max_angular_velocity", "capture_radius",
    ])
    def test_string_instead_of_float_raises_error(self, field_name):
        data = {**VALID_CONFIG, field_name: "not_a_number"}
        with pytest.raises(ConfigValidationError) as exc_info:
            _load(data)
        assert field_name in str(exc_info.value)

    @pytest.mark.parametrize("field_name", ["random_seed", "max_steps", "tau"])
    def test_float_instead_of_int_raises_error(self, field_name):
        data = {**VALID_CONFIG, field_name: 3.5}
        with pytest.raises(ConfigValidationError) as exc_info:
            _load(data)
        assert field_name in str(exc_info.value)

    @pytest.mark.parametrize("field_name", ["random_seed", "max_steps", "tau"])
    def test_string_instead_of_int_raises_error(self, field_name):
        data = {**VALID_CONFIG, field_name: "bad"}
        with pytest.raises(ConfigValidationError) as exc_info:
            _load(data)
        assert field_name in str(exc_info.value)


# ---------------------------------------------------------------------------
# Obstacle parsing — valid shapes
# ---------------------------------------------------------------------------

class TestObstacleParsing:
    def test_rect_obstacle_parses(self):
        data = {
            **VALID_CONFIG,
            "obstacles": [
                {"type": "rect", "cx": 200.0, "cy": 300.0,
                 "width": 60.0, "height": 20.0, "angle": 0.0}
            ],
        }
        cfg = _load(data)
        assert len(cfg.obstacles) == 1
        assert cfg.obstacles[0]["type"] == "rect"

    def test_circle_obstacle_parses(self):
        data = {
            **VALID_CONFIG,
            "obstacles": [
                {"type": "circle", "cx": 500.0, "cy": 200.0, "radius": 30.0}
            ],
        }
        cfg = _load(data)
        assert len(cfg.obstacles) == 1
        assert cfg.obstacles[0]["type"] == "circle"

    def test_polygon_obstacle_parses(self):
        data = {
            **VALID_CONFIG,
            "obstacles": [
                {"type": "polygon",
                 "vertices": [[400.0, 100.0], [450.0, 150.0], [380.0, 160.0]]}
            ],
        }
        cfg = _load(data)
        assert len(cfg.obstacles) == 1
        assert cfg.obstacles[0]["type"] == "polygon"

    def test_all_three_obstacle_types_together(self):
        data = {
            **VALID_CONFIG,
            "obstacles": [
                {"type": "rect", "cx": 200.0, "cy": 300.0,
                 "width": 60.0, "height": 20.0, "angle": 0.0},
                {"type": "circle", "cx": 500.0, "cy": 200.0, "radius": 30.0},
                {"type": "polygon",
                 "vertices": [[400.0, 100.0], [450.0, 150.0], [380.0, 160.0]]},
            ],
        }
        cfg = _load(data)
        assert len(cfg.obstacles) == 3


# ---------------------------------------------------------------------------
# Obstacle validation — invalid shapes
# ---------------------------------------------------------------------------

class TestInvalidObstacles:
    def test_rect_zero_width_raises_invalid_obstacle_error(self):
        data = {
            **VALID_CONFIG,
            "obstacles": [
                {"type": "rect", "cx": 100.0, "cy": 100.0,
                 "width": 0.0, "height": 20.0, "angle": 0.0}
            ],
        }
        with pytest.raises(InvalidObstacleError):
            _load(data)

    def test_rect_negative_height_raises_invalid_obstacle_error(self):
        data = {
            **VALID_CONFIG,
            "obstacles": [
                {"type": "rect", "cx": 100.0, "cy": 100.0,
                 "width": 20.0, "height": -5.0, "angle": 0.0}
            ],
        }
        with pytest.raises(InvalidObstacleError):
            _load(data)

    def test_circle_negative_radius_raises_invalid_obstacle_error(self):
        data = {
            **VALID_CONFIG,
            "obstacles": [
                {"type": "circle", "cx": 100.0, "cy": 100.0, "radius": -10.0}
            ],
        }
        with pytest.raises(InvalidObstacleError):
            _load(data)

    def test_circle_zero_radius_raises_invalid_obstacle_error(self):
        data = {
            **VALID_CONFIG,
            "obstacles": [
                {"type": "circle", "cx": 100.0, "cy": 100.0, "radius": 0.0}
            ],
        }
        with pytest.raises(InvalidObstacleError):
            _load(data)

    def test_polygon_fewer_than_3_vertices_raises_invalid_obstacle_error(self):
        data = {
            **VALID_CONFIG,
            "obstacles": [
                {"type": "polygon", "vertices": [[0.0, 0.0], [1.0, 1.0]]}
            ],
        }
        with pytest.raises(InvalidObstacleError):
            _load(data)

    def test_polygon_missing_vertices_raises_invalid_obstacle_error(self):
        data = {
            **VALID_CONFIG,
            "obstacles": [{"type": "polygon"}],
        }
        with pytest.raises(InvalidObstacleError):
            _load(data)

    def test_rect_missing_width_raises_invalid_obstacle_error(self):
        data = {
            **VALID_CONFIG,
            "obstacles": [
                {"type": "rect", "cx": 100.0, "cy": 100.0, "height": 20.0, "angle": 0.0}
            ],
        }
        with pytest.raises(InvalidObstacleError):
            _load(data)

    def test_circle_missing_radius_raises_invalid_obstacle_error(self):
        data = {
            **VALID_CONFIG,
            "obstacles": [{"type": "circle", "cx": 100.0, "cy": 100.0}],
        }
        with pytest.raises(InvalidObstacleError):
            _load(data)

    def test_invalid_obstacle_is_subclass_of_config_validation_error(self):
        data = {
            **VALID_CONFIG,
            "obstacles": [
                {"type": "circle", "cx": 100.0, "cy": 100.0, "radius": -1.0}
            ],
        }
        with pytest.raises(ConfigValidationError):
            _load(data)


# ---------------------------------------------------------------------------
# File not found
# ---------------------------------------------------------------------------

class TestFileNotFound:
    def test_missing_file_raises_file_not_found_error(self):
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load("/nonexistent/path/config.json")
