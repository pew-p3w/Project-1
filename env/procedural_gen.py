"""Procedural generator for the Dec-POMDP environment.

Places AgentA, AgentB, Target, and Obstacles at valid float positions
within world bounds using a seeded random.Random instance for full
reproducibility.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from env.config_loader import EnvConfig
from env.errors import GenerationFailedError
from env.objects import AgentA, AgentB, CircleDef, Obstacle, PolygonDef, RectDef, Target
from env.physics_engine import PhysicsEngine


@dataclass
class GeneratedLayout:
    agent_a: AgentA
    agent_b: AgentB
    target: Target
    obstacles: list[Obstacle]


_MAX_RETRIES = 1000


class ProceduralGenerator:
    """Generates a valid episode layout using a seeded RNG.

    Uses ``random.Random(seed)`` (not global state) so generation is
    fully reproducible and independent of any other random usage.
    """

    def __init__(self, config: EnvConfig) -> None:
        self._config = config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, seed: int) -> GeneratedLayout:
        """Place all entities and register obstacles with a fresh PhysicsEngine.

        Returns a GeneratedLayout with fully initialised entities.
        Raises GenerationFailedError if constraints cannot be satisfied
        within _MAX_RETRIES attempts.
        """
        cfg = self._config
        rng = random.Random(seed)

        margin = cfg.agent_radius
        x_lo = margin
        x_hi = cfg.world_width - margin
        y_lo = margin
        y_hi = cfg.world_height - margin

        if x_lo >= x_hi or y_lo >= y_hi:
            raise GenerationFailedError(
                f"World too small for agent_radius={cfg.agent_radius}: "
                f"seed={seed}, world={cfg.world_width}x{cfg.world_height}"
            )

        obstacles = self._build_obstacles(rng, cfg)

        for attempt in range(_MAX_RETRIES):
            ax = rng.uniform(x_lo, x_hi)
            ay = rng.uniform(y_lo, y_hi)

            bx = rng.uniform(x_lo, x_hi)
            by = rng.uniform(y_lo, y_hi)

            tx = rng.uniform(x_lo, x_hi)
            ty = rng.uniform(y_lo, y_hi)

            dist_bt = math.hypot(bx - tx, by - ty)

            if dist_bt <= cfg.capture_radius:
                continue

            if cfg.min_separation > 0.0 and dist_bt < cfg.min_separation:
                continue

            # All constraints satisfied
            agent_a = AgentA(id="agent_a", x=ax, y=ay)
            agent_b = AgentB(id="agent_b", x=bx, y=by)
            target = Target(id="target", x=tx, y=ty)

            # Register obstacles with a fresh PhysicsEngine
            physics = PhysicsEngine(cfg)
            for obs in obstacles:
                physics.add_obstacle(obs.shape_def)
            physics.add_agent_b(bx, by, cfg.agent_radius)

            return GeneratedLayout(
                agent_a=agent_a,
                agent_b=agent_b,
                target=target,
                obstacles=obstacles,
            )

        raise GenerationFailedError(
            f"ProceduralGenerator failed after {_MAX_RETRIES} attempts: "
            f"seed={seed}, capture_radius={cfg.capture_radius}, "
            f"min_separation={cfg.min_separation}, "
            f"world={cfg.world_width}x{cfg.world_height}"
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_obstacles(
        self, rng: random.Random, cfg: EnvConfig
    ) -> list[Obstacle]:
        """Build obstacle entities from explicit config list or procedurally."""
        if cfg.obstacles:
            return self._obstacles_from_config(cfg.obstacles)
        if cfg.procedural:
            return self._obstacles_procedural(rng, cfg)
        return []

    def _obstacles_from_config(self, obs_list: list[dict]) -> list[Obstacle]:
        """Parse explicit obstacle dicts into Obstacle entities."""
        result: list[Obstacle] = []
        for i, obs_dict in enumerate(obs_list):
            obs_type = obs_dict["type"]
            if obs_type == "rect":
                shape_def = RectDef(
                    cx=float(obs_dict["cx"]),
                    cy=float(obs_dict["cy"]),
                    width=float(obs_dict["width"]),
                    height=float(obs_dict["height"]),
                    angle=float(obs_dict["angle"]),
                )
                cx, cy = shape_def.cx, shape_def.cy
            elif obs_type == "circle":
                shape_def = CircleDef(
                    cx=float(obs_dict["cx"]),
                    cy=float(obs_dict["cy"]),
                    radius=float(obs_dict["radius"]),
                )
                cx, cy = shape_def.cx, shape_def.cy
            elif obs_type == "polygon":
                verts = [tuple(v) for v in obs_dict["vertices"]]
                shape_def = PolygonDef(vertices=verts)
                # Use centroid as obstacle position
                cx = sum(v[0] for v in verts) / len(verts)
                cy = sum(v[1] for v in verts) / len(verts)
            else:
                raise ValueError(f"Unknown obstacle type: {obs_type!r}")

            result.append(
                Obstacle(id=f"obstacle_{i}", x=cx, y=cy, shape_def=shape_def)
            )
        return result

    def _obstacles_procedural(
        self, rng: random.Random, cfg: EnvConfig
    ) -> list[Obstacle]:
        """Generate random circle obstacles from procedural config block."""
        proc = cfg.procedural
        count = int(proc.get("count", 0))
        min_r = float(proc.get("min_radius", 5.0))
        max_r = float(proc.get("max_radius", 20.0))

        result: list[Obstacle] = []
        for i in range(count):
            r = rng.uniform(min_r, max_r)
            cx = rng.uniform(r, cfg.world_width - r)
            cy = rng.uniform(r, cfg.world_height - r)
            shape_def = CircleDef(cx=cx, cy=cy, radius=r)
            result.append(
                Obstacle(id=f"obstacle_{i}", x=cx, y=cy, shape_def=shape_def)
            )
        return result
