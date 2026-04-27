"""Property-based tests for the velocity-based movement system.

# Feature: dec-pomdp-environment, Property 4: Agent_B Velocity Magnitude Never Exceeds max_speed
# Feature: dec-pomdp-environment, Property 5: Heading Change Clamped to max_angular_velocity
"""

import math

from hypothesis import given, settings
from hypothesis import strategies as st

from env.movement import apply_steering

# ---------------------------------------------------------------------------
# Constants used across tests
# ---------------------------------------------------------------------------

MAX_SPEED = 150.0
MAX_ANGULAR_VELOCITY = 0.5


# ---------------------------------------------------------------------------
# Property 4: Agent_B Velocity Magnitude Never Exceeds max_speed
# Validates: Requirements 5.2
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(
    actions=st.lists(
        st.tuples(st.floats(-1.0, 1.0), st.floats(-50.0, 50.0)),
        min_size=1,
        max_size=50,
    )
)
def test_velocity_magnitude_never_exceeds_max_speed(actions):
    # Feature: dec-pomdp-environment, Property 4: Agent_B Velocity Magnitude Never Exceeds max_speed
    heading = 0.0
    speed = 0.0

    for delta_heading, delta_speed in actions:
        heading, speed, vx, vy = apply_steering(
            heading, speed, delta_heading, delta_speed,
            MAX_ANGULAR_VELOCITY, MAX_SPEED,
        )
        magnitude = math.sqrt(vx ** 2 + vy ** 2)
        assert magnitude <= MAX_SPEED + 1e-9, (
            f"Velocity magnitude {magnitude} exceeded max_speed {MAX_SPEED} "
            f"after action ({delta_heading}, {delta_speed})"
        )


# ---------------------------------------------------------------------------
# Property 5: Heading Change Clamped to max_angular_velocity
# Validates: Requirements 5.2
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(
    heading=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
    delta_heading=st.floats(allow_nan=False, allow_infinity=False),
)
def test_heading_change_clamped_to_max_angular_velocity(heading, delta_heading):
    # Feature: dec-pomdp-environment, Property 5: Heading Change Clamped to max_angular_velocity
    new_heading, speed, vx, vy = apply_steering(
        heading, 0.0, delta_heading, 0.0,
        MAX_ANGULAR_VELOCITY, MAX_SPEED,
    )
    actual_change = abs(new_heading - heading)
    assert actual_change <= MAX_ANGULAR_VELOCITY + 1e-9, (
        f"|heading_new - heading_old| = {actual_change} exceeded "
        f"max_angular_velocity {MAX_ANGULAR_VELOCITY} for delta_heading={delta_heading}"
    )
