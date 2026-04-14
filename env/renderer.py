"""Optional Pygame renderer for the Dec-POMDP environment.

Only imported when config.render is True, so Pygame is never loaded in
headless runs.
"""

from __future__ import annotations

import pygame

from env.config_loader import EnvConfig


class Renderer:
    """Opens a Pygame window and draws the environment state each step."""

    # Colours
    _BG_COLOR = (30, 30, 30)
    _AGENT_B_COLOR = (0, 120, 255)   # blue
    _AGENT_A_COLOR = (0, 220, 80)    # green
    _TARGET_COLOR = (255, 220, 0)    # yellow
    _RECT_COLOR = (220, 40, 40)      # red
    _CIRCLE_COLOR = (255, 140, 0)    # orange
    _POLYGON_COLOR = (160, 0, 220)   # purple

    def __init__(self, config: EnvConfig) -> None:
        """Open Pygame window sized to world_width × world_height."""
        self._config = config
        pygame.init()
        self._width = int(config.world_width)
        self._height = int(config.world_height)
        self._screen = pygame.display.set_mode((self._width, self._height))
        pygame.display.set_caption("Dec-POMDP Environment")
        self._clock = pygame.time.Clock()

    def draw(self, state: dict) -> bool:
        """Render current state. Returns False if window was closed by user.

        Args:
            state: dict with keys agent_b, agent_b_velocity, target,
                   obstacles, timestep, last_reward, terminated.
        """
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

        self._screen.fill(self._BG_COLOR)

        # Draw obstacles
        for obs in state.get("obstacles", []):
            self._draw_obstacle(obs)

        # Draw target (capture zone)
        target = state.get("target")
        if target is not None:
            tx, ty = int(target[0]), int(target[1])
            r = int(self._config.capture_radius)
            pygame.draw.circle(self._screen, self._TARGET_COLOR, (tx, ty), max(r, 1))

        # Draw Agent B (blue circle)
        agent_b = state.get("agent_b")
        if agent_b is not None:
            bx, by = int(agent_b[0]), int(agent_b[1])
            r = int(self._config.agent_radius)
            pygame.draw.circle(self._screen, self._AGENT_B_COLOR, (bx, by), max(r, 1))

        # Agent A position is not in state_dict — draw at fixed top-left corner marker
        pygame.draw.circle(self._screen, self._AGENT_A_COLOR, (20, 20), 8)

        # Update window title with timestep and reward
        timestep = state.get("timestep", 0)
        last_reward = state.get("last_reward", 0.0)
        pygame.display.set_caption(
            f"Dec-POMDP | t={timestep} | r={last_reward:.2f}"
        )

        pygame.display.flip()
        self._clock.tick(60)
        return True

    def close(self) -> None:
        """Destroy Pygame window and quit Pygame."""
        pygame.quit()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _draw_obstacle(self, obs: dict) -> None:
        obs_type = obs.get("type")
        if obs_type == "rect":
            cx = int(obs["cx"])
            cy = int(obs["cy"])
            w = int(obs["width"])
            h = int(obs["height"])
            rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
            pygame.draw.rect(self._screen, self._RECT_COLOR, rect)
        elif obs_type == "circle":
            cx = int(obs["cx"])
            cy = int(obs["cy"])
            r = max(int(obs["radius"]), 1)
            pygame.draw.circle(self._screen, self._CIRCLE_COLOR, (cx, cy), r)
        elif obs_type == "polygon":
            verts = [(int(v[0]), int(v[1])) for v in obs["vertices"]]
            if len(verts) >= 3:
                pygame.draw.polygon(self._screen, self._POLYGON_COLOR, verts)
