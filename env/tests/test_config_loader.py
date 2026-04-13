"""Unit tests for ConfigLoader and EnvConfig."""

import json
import os
import tempfile

import pytest

from env.config_loader import REQUIRED_FIELDS, ConfigLoader, EnvConfig
from env.errors import ConfigValidationError

VALID_CONFIG = {
    "grid_width": 64,
    "grid_height": 64,
    "num_obstacles": 20,
    "random_seed": 42,
    "max_steps": 500,
    "tau": 3,
    "min_separation": 5,
    "message_dim": 16,
    "debug": False,
    "log_level": "INFO",
}


def write_config(data: dict) -> str:
    """Write a dict to a temp JSON file and return the path."""
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    )
    json.dump(data, f)
    f.close()
    return f.name


class TestValidConfig:
    def test_loads_all_fields_correctly(self):
        path = write_config(VALID_CONFIG)
        try:
            cfg = ConfigLoader.load(path)
            assert cfg.grid_width == 64
            assert cfg.grid_height == 64
            assert cfg.num_obstacles == 20
            assert cfg.random_seed == 42
            assert cfg.max_steps == 500
            assert cfg.tau == 3
            assert cfg.min_separation == 5
            assert cfg.message_dim == 16
            assert cfg.debug is False
            assert cfg.log_level == "INFO"
        finally:
            os.unlink(path)

    def test_returns_envconfig_instance(self):
        path = write_config(VALID_CONFIG)
        try:
            cfg = ConfigLoader.load(path)
            assert isinstance(cfg, EnvConfig)
        finally:
            os.unlink(path)


class TestOptionalFieldDefaults:
    def _minimal_config(self):
        return {k: VALID_CONFIG[k] for k in REQUIRED_FIELDS}

    def test_min_separation_defaults_to_zero(self):
        path = write_config(self._minimal_config())
        try:
            cfg = ConfigLoader.load(path)
            assert cfg.min_separation == 0
        finally:
            os.unlink(path)

    def test_message_dim_defaults_to_16(self):
        path = write_config(self._minimal_config())
        try:
            cfg = ConfigLoader.load(path)
            assert cfg.message_dim == 16
        finally:
            os.unlink(path)

    def test_debug_defaults_to_false(self):
        path = write_config(self._minimal_config())
        try:
            cfg = ConfigLoader.load(path)
            assert cfg.debug is False
        finally:
            os.unlink(path)

    def test_log_level_defaults_to_info(self):
        path = write_config(self._minimal_config())
        try:
            cfg = ConfigLoader.load(path)
            assert cfg.log_level == "INFO"
        finally:
            os.unlink(path)


class TestMissingRequiredFields:
    @pytest.mark.parametrize("field", REQUIRED_FIELDS)
    def test_missing_field_raises_config_validation_error(self, field):
        data = {k: VALID_CONFIG[k] for k in VALID_CONFIG if k != field}
        path = write_config(data)
        try:
            with pytest.raises(ConfigValidationError) as exc_info:
                ConfigLoader.load(path)
            assert field in str(exc_info.value)
        finally:
            os.unlink(path)


class TestWrongTypes:
    @pytest.mark.parametrize("field", REQUIRED_FIELDS)
    def test_string_value_for_int_field_raises_error(self, field):
        data = {**VALID_CONFIG, field: "not_an_int"}
        path = write_config(data)
        try:
            with pytest.raises(ConfigValidationError) as exc_info:
                ConfigLoader.load(path)
            assert field in str(exc_info.value)
        finally:
            os.unlink(path)

    def test_bool_rejected_for_int_field(self):
        # bool is a subclass of int in Python; we must reject it explicitly
        data = {**VALID_CONFIG, "grid_width": True}
        path = write_config(data)
        try:
            with pytest.raises(ConfigValidationError) as exc_info:
                ConfigLoader.load(path)
            assert "grid_width" in str(exc_info.value)
        finally:
            os.unlink(path)

    def test_int_rejected_for_debug_bool_field(self):
        # debug expects bool; an int should raise an error
        data = {**VALID_CONFIG, "debug": 1}
        path = write_config(data)
        try:
            with pytest.raises(ConfigValidationError) as exc_info:
                ConfigLoader.load(path)
            assert "debug" in str(exc_info.value)
        finally:
            os.unlink(path)


class TestFileNotFound:
    def test_missing_file_raises_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load("/nonexistent/path/config.json")
