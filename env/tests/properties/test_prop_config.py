"""Property-based tests for ConfigLoader.

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

# Validates: Requirements 1.3

VALID_BASE = {
    "grid_width": 64,
    "grid_height": 64,
    "num_obstacles": 20,
    "random_seed": 42,
    "max_steps": 500,
    "tau": 3,
}


def write_config(data: dict) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(data, f)
    f.close()
    return f.name


@settings(max_examples=100)
@given(field=st.sampled_from(REQUIRED_FIELDS))
def test_missing_required_field_error_names_field(field):
    """Property 1: Config Error Names the Offending Field — missing field case.

    Validates: Requirements 1.3
    """
    data = {k: v for k, v in VALID_BASE.items() if k != field}
    path = write_config(data)
    try:
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigLoader.load(path)
        assert field in str(exc_info.value), (
            f"ConfigValidationError message did not contain field name '{field}': "
            f"{exc_info.value}"
        )
    finally:
        os.unlink(path)


@settings(max_examples=100)
@given(field=st.sampled_from(REQUIRED_FIELDS))
def test_wrong_type_required_field_error_names_field(field):
    """Property 1: Config Error Names the Offending Field — wrong type case.

    Validates: Requirements 1.3
    """
    # Replace the field value with a string (wrong type for all required int fields)
    data = {**VALID_BASE, field: "wrong_type"}
    path = write_config(data)
    try:
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigLoader.load(path)
        assert field in str(exc_info.value), (
            f"ConfigValidationError message did not contain field name '{field}': "
            f"{exc_info.value}"
        )
    finally:
        os.unlink(path)
