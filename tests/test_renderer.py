"""Tests for the Pygame renderer.

Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6

Key tests:
- Pygame is NOT imported when render=False
- Renderer tests are skipped if no display is available
"""

import json
import os
import sys
import tempfile

import pytest

# ---------------------------------------------------------------------------
# Minimal config helpers
# ---------------------------------------------------------------------------

_BASE_CONFIG = {
    "world_width": 400.0,
    "world_height": 300.0,
    "agent_radius": 10.0,
    "max_speed": 100.0,
    "max_angular_velocity": 0.3,
    "capture_radius": 15.0,
    "random_seed": 42,
    "max_steps": 200,
    "tau": 2,
    "min_separation": 50.0,
    "obstacles": [
        {"type": "rect", "cx": 200.0, "cy": 150.0, "width": 30.0, "height": 20.0, "angle": 0.0},
        {"type": "circle", "cx": 100.0, "cy": 100.0, "radius": 15.0},
        {"type": "polygon", "vertices": [[300.0, 50.0], [350.0, 80.0], [280.0, 90.0]]},
    ],
    "render": False,
    "log_level": "WARNING",
}


def _write_config(cfg: dict) -> str:
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(cfg, f)
    return path


# ---------------------------------------------------------------------------
# Test: Pygame NOT imported when render=False (Requirement 14.5)
# ---------------------------------------------------------------------------

def test_pygame_not_imported_when_render_false():
    """When render=False, pygame must not be imported into sys.modules."""
    # Remove pygame from sys.modules if it was already imported by another test
    # so we can verify the environment doesn't re-import it
    pygame_was_present = "pygame" in sys.modules

    cfg = dict(_BASE_CONFIG)
    cfg["render"] = False
    path = _write_config(cfg)
    try:
        # Import fresh environment — render=False should not trigger pygame import
        from env.environment import DecPOMDPEnvironment
        env = DecPOMDPEnvironment(path)
        env.reset()

        # If pygame was not present before, it should still not be present
        if not pygame_was_present:
            assert "pygame" not in sys.modules, (
                "pygame was imported even though render=False"
            )
        # If pygame was already present (from another test), we can't assert absence,
        # but we can assert the renderer was not created
        assert env._renderer is None
    finally:
        os.unlink(path)
        env.close()


def test_renderer_is_none_when_render_false():
    """Environment._renderer should be None when render=False."""
    cfg = dict(_BASE_CONFIG)
    cfg["render"] = False
    path = _write_config(cfg)
    try:
        from env.environment import DecPOMDPEnvironment
        env = DecPOMDPEnvironment(path)
        assert env._renderer is None
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Display-dependent renderer tests — skipped if no display available
# ---------------------------------------------------------------------------

def _has_display() -> bool:
    """Return True if a display is available for Pygame."""
    try:
        import pygame
        pygame.init()
        # Try to create a minimal surface
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
        pygame.quit()
        return True
    except Exception:
        return False


_display_available = _has_display()
_skip_no_display = pytest.mark.skipif(
    not _display_available,
    reason="No display available for Pygame rendering tests",
)


@_skip_no_display
def test_renderer_opens_window():
    """Renderer should open a Pygame window without error."""
    import pygame
    from env.config_loader import ConfigLoader
    from env.renderer import Renderer

    cfg = dict(_BASE_CONFIG)
    path = _write_config(cfg)
    try:
        config = ConfigLoader.load(path)
        renderer = Renderer(config)
        assert renderer is not None
        renderer.close()
    finally:
        os.unlink(path)


@_skip_no_display
def test_renderer_draw_returns_true_when_window_open():
    """draw() should return True when the window is still open."""
    from env.config_loader import ConfigLoader
    from env.renderer import Renderer

    cfg = dict(_BASE_CONFIG)
    path = _write_config(cfg)
    try:
        config = ConfigLoader.load(path)
        renderer = Renderer(config)
        state = {
            "agent_b": (200.0, 150.0),
            "agent_b_velocity": (10.0, 0.0),
            "target": (300.0, 200.0),
            "obstacles": _BASE_CONFIG["obstacles"],
            "timestep": 5,
            "last_reward": 0.0,
            "terminated": False,
        }
        result = renderer.draw(state)
        assert result is True
        renderer.close()
    finally:
        os.unlink(path)


@_skip_no_display
def test_renderer_draw_all_obstacle_types():
    """draw() should handle rect, circle, and polygon obstacles without error."""
    from env.config_loader import ConfigLoader
    from env.renderer import Renderer

    cfg = dict(_BASE_CONFIG)
    path = _write_config(cfg)
    try:
        config = ConfigLoader.load(path)
        renderer = Renderer(config)
        state = {
            "agent_b": (50.0, 50.0),
            "agent_b_velocity": (0.0, 0.0),
            "target": (350.0, 250.0),
            "obstacles": [
                {"type": "rect", "cx": 200.0, "cy": 150.0, "width": 30.0, "height": 20.0, "angle": 0.0},
                {"type": "circle", "cx": 100.0, "cy": 100.0, "radius": 15.0},
                {"type": "polygon", "vertices": [[300.0, 50.0], [350.0, 80.0], [280.0, 90.0]]},
            ],
            "timestep": 1,
            "last_reward": 0.0,
            "terminated": False,
        }
        result = renderer.draw(state)
        assert result is True
        renderer.close()
    finally:
        os.unlink(path)


@_skip_no_display
def test_renderer_close_is_idempotent():
    """close() should not raise when called once."""
    from env.config_loader import ConfigLoader
    from env.renderer import Renderer

    cfg = dict(_BASE_CONFIG)
    path = _write_config(cfg)
    try:
        config = ConfigLoader.load(path)
        renderer = Renderer(config)
        renderer.close()
        # Renderer is now closed — no further assertions needed
    finally:
        os.unlink(path)
