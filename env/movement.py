"""Velocity-based movement system for Agent B in the Dec-POMDP environment."""

from __future__ import annotations

import math


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp value to [lo, hi]."""
    return max(lo, min(hi, value))


def apply_steering(
    heading: float,
    speed: float,
    delta_heading: float,
    delta_speed: float,
    max_angular_velocity: float,
    max_speed: float,
) -> tuple[float, float, float, float]:
    """Apply steering action to Agent B's heading and speed.

    Returns (new_heading, new_speed, new_vx, new_vy).

    - Clamps delta_heading to [-max_angular_velocity, +max_angular_velocity]
    - Clamps resulting speed to [0, max_speed]
    - Computes vx = new_speed * cos(new_heading)
    - Computes vy = new_speed * sin(new_heading)
    """
    clamped_delta = clamp(delta_heading, -max_angular_velocity, max_angular_velocity)
    new_heading = heading + clamped_delta
    new_speed = clamp(speed + delta_speed, 0.0, max_speed)
    new_vx = new_speed * math.cos(new_heading)
    new_vy = new_speed * math.sin(new_heading)
    return new_heading, new_speed, new_vx, new_vy
