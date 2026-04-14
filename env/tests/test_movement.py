"""Unit tests for env/movement.py — velocity-based movement system."""

import math
import pytest

from env.movement import apply_steering, clamp


# ---------------------------------------------------------------------------
# clamp helper
# ---------------------------------------------------------------------------

def test_clamp_within_range():
    assert clamp(5.0, 0.0, 10.0) == 5.0


def test_clamp_at_lo():
    assert clamp(0.0, 0.0, 10.0) == 0.0


def test_clamp_at_hi():
    assert clamp(10.0, 0.0, 10.0) == 10.0


def test_clamp_below_lo():
    assert clamp(-1.0, 0.0, 10.0) == 0.0


def test_clamp_above_hi():
    assert clamp(11.0, 0.0, 10.0) == 10.0


# ---------------------------------------------------------------------------
# apply_steering — heading
# ---------------------------------------------------------------------------

def test_zero_action_leaves_heading_unchanged():
    heading, speed, vx, vy = apply_steering(1.0, 5.0, 0.0, 0.0, 0.5, 20.0)
    assert heading == pytest.approx(1.0)


def test_zero_action_leaves_speed_unchanged():
    heading, speed, vx, vy = apply_steering(1.0, 5.0, 0.0, 0.0, 0.5, 20.0)
    assert speed == pytest.approx(5.0)


def test_positive_delta_heading_within_limit_increases_heading():
    heading, speed, vx, vy = apply_steering(0.0, 0.0, 0.3, 0.0, 0.5, 20.0)
    assert heading == pytest.approx(0.3)


def test_negative_delta_heading_within_limit_decreases_heading():
    heading, speed, vx, vy = apply_steering(1.0, 0.0, -0.3, 0.0, 0.5, 20.0)
    assert heading == pytest.approx(0.7)


def test_delta_heading_larger_than_max_is_clamped_to_max():
    max_av = 0.5
    heading, speed, vx, vy = apply_steering(0.0, 0.0, 2.0, 0.0, max_av, 20.0)
    assert heading == pytest.approx(max_av)


def test_delta_heading_smaller_than_neg_max_is_clamped_to_neg_max():
    max_av = 0.5
    heading, speed, vx, vy = apply_steering(0.0, 0.0, -2.0, 0.0, max_av, 20.0)
    assert heading == pytest.approx(-max_av)


# ---------------------------------------------------------------------------
# apply_steering — speed
# ---------------------------------------------------------------------------

def test_positive_delta_speed_increases_speed():
    heading, speed, vx, vy = apply_steering(0.0, 5.0, 0.0, 3.0, 0.5, 20.0)
    assert speed == pytest.approx(8.0)


def test_delta_speed_exceeding_max_speed_is_clamped():
    heading, speed, vx, vy = apply_steering(0.0, 18.0, 0.0, 5.0, 0.5, 20.0)
    assert speed == pytest.approx(20.0)


def test_negative_delta_speed_decreases_speed():
    heading, speed, vx, vy = apply_steering(0.0, 10.0, 0.0, -3.0, 0.5, 20.0)
    assert speed == pytest.approx(7.0)


def test_delta_speed_below_zero_is_clamped_to_zero():
    heading, speed, vx, vy = apply_steering(0.0, 2.0, 0.0, -5.0, 0.5, 20.0)
    assert speed == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# apply_steering — velocity vector
# ---------------------------------------------------------------------------

def test_vx_equals_speed_times_cos_heading():
    h, s, vx, vy = apply_steering(0.7, 8.0, 0.0, 0.0, 0.5, 20.0)
    assert vx == pytest.approx(8.0 * math.cos(0.7))


def test_vy_equals_speed_times_sin_heading():
    h, s, vx, vy = apply_steering(0.7, 8.0, 0.0, 0.0, 0.5, 20.0)
    assert vy == pytest.approx(8.0 * math.sin(0.7))


def test_zero_speed_positive_delta_speed_produces_correct_velocity():
    h, s, vx, vy = apply_steering(math.pi / 4, 0.0, 0.0, 10.0, 0.5, 20.0)
    assert vx == pytest.approx(10.0 * math.cos(math.pi / 4))
    assert vy == pytest.approx(10.0 * math.sin(math.pi / 4))


def test_heading_zero_speed_10_gives_vx_10_vy_0():
    h, s, vx, vy = apply_steering(0.0, 10.0, 0.0, 0.0, 0.5, 20.0)
    assert vx == pytest.approx(10.0)
    assert vy == pytest.approx(0.0, abs=1e-10)


def test_heading_pi_over_2_speed_10_gives_vx_approx_0_vy_10():
    h, s, vx, vy = apply_steering(math.pi / 2, 10.0, 0.0, 0.0, 0.5, 20.0)
    assert vx == pytest.approx(0.0, abs=1e-10)
    assert vy == pytest.approx(10.0)
