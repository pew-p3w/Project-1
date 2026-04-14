"""Property-based tests for config_loader.py.

# Feature: dec-pomdp-environment, Property 1: Config Error Names the Offending Field
"""

import json
import os
import tempfile

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from env.config_loader import REQUIRED_FIELDS, ConfigLoader
from env.errors import ConfigValidationError


# ---------------------------------------------------------------------------
# Base valid config used as a template
# ---------------------------------------------------------------------------

_BASE_CONFIG = {
    "world_width": 800.0,
    "world_height": 600.0,
    "agent_radius": 10.0,
    "max_speed": 150.0,
    "max_angular_velocity": 0.2,
    "capture_radius": 20.0,
    "random_seed": 42,
    "max_steps": 500,
    "tau": 3,
}


def _write_and_load(data: dict):
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
    try:
        return ConfigLoader.load(path)
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Property 1: Config Error Names the Offending Field
# Validates: Requirements 1.5
# ---------------------------------------------------------------------------

@given(field_name=st.sampled_from(REQUIRED_FIELDS))
@settings(max_examples=100)
def test_missing_field_error_names_offending_field(field_name):
    """For any required field, omitting it must raise ConfigValidationError
    whose message contains the exact field name.

    # Feature: dec-pomdp-environment, Property 1: Config Error Names the Offending Field
    """
    data = {k: v for k, v in _BASE_CONFIG.items() if k != field_name}
    with pytest.raises(ConfigValidationError) as exc_info:
        _write_and_load(data)
    assert field_name in str(exc_info.value), (
        f"Expected field name '{field_name}' in error message, "
        f"but got: '{exc_info.value}'"
    )


@given(field_name=st.sampled_from(REQUIRED_FIELDS))
@settings(max_examples=100)
def test_wrong_type_field_error_names_offending_field(field_name):
    """For any required field, providing a wrong type must raise
    ConfigValidationError whose message contains the exact field name.

    # Feature: dec-pomdp-environment, Property 1: Config Error Names the Offending Field
    """
    # Replace the field value with a string (always wrong for numeric fields)
    data = {**_BASE_CONFIG, field_name: "invalid_value"}
    with pytest.raises(ConfigValidationError) as exc_info:
        _write_and_load(data)
    assert field_name in str(exc_info.value), (
        f"Expected field name '{field_name}' in error message, "
        f"but got: '{exc_info.value}'"
    )
