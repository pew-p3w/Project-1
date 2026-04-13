"""Procedural generator for the Dec-POMDP environment.

Places AgentA, AgentB, Target, and Obstacles at valid, non-overlapping
grid positions using a seeded random.Random instance for reproducibility.
"""

import random

from env.config_loader import EnvConfig
from env.entity import Entity
from env.errors import GenerationFailedError
from env.objects import AgentA, AgentB, Obstacle, Target

_MAX_RETRIES = 1000


class ProceduralGenerator:
    """Generates a fresh entity layout for each episode.

    Args:
        config: Validated environment configuration.
    """

    def __init__(self, config: EnvConfig) -> None:
        self._config = config

    def generate(self, seed: int) -> list[Entity]:
        """Place all entities at valid positions using the given seed.

        Uses ``random.Random(seed)`` (not global state) so results are
        fully reproducible and independent of any other random usage.

        Args:
            seed: Integer seed for the RNG.

        Returns:
            A list of entities: 1 AgentA, 1 AgentB, 1 Target, N Obstacles.

        Raises:
            GenerationFailedError: If a valid layout cannot be found within
                the retry limit.
        """
        cfg = self._config
        rng = random.Random(seed)

        def rand_pos() -> tuple[int, int]:
            x = rng.randint(0, cfg.grid_width - 1)
            y = rng.randint(0, cfg.grid_height - 1)
            return (x, y)

        for attempt in range(_MAX_RETRIES):
            # --- Place AgentA (non-collidable, no constraints with others) ---
            agent_a_pos = rand_pos()

            # --- Place Target ---
            target_pos = rand_pos()

            # --- Place AgentB ---
            # Must differ from Target; must satisfy min_separation if set.
            agent_b_pos = rand_pos()
            if agent_b_pos == target_pos:
                continue
            if cfg.min_separation > 0:
                dist = abs(agent_b_pos[0] - target_pos[0]) + abs(agent_b_pos[1] - target_pos[1])
                if dist < cfg.min_separation:
                    continue

            # --- Place Obstacles ---
            # Collidable entities (AgentB + Obstacles) must not share positions.
            collidable_positions: set[tuple[int, int]] = {agent_b_pos}
            obstacles: list[tuple[int, int]] = []
            conflict = False
            for _ in range(cfg.num_obstacles):
                obs_pos = rand_pos()
                if obs_pos in collidable_positions:
                    conflict = True
                    break
                collidable_positions.add(obs_pos)
                obstacles.append(obs_pos)

            if conflict:
                continue

            # --- All constraints satisfied — build entity list ---
            entities: list[Entity] = [
                AgentA("agent_a", agent_a_pos[0], agent_a_pos[1]),
                AgentB("agent_b", agent_b_pos[0], agent_b_pos[1]),
                Target("target", target_pos[0], target_pos[1]),
            ]
            for i, (ox, oy) in enumerate(obstacles):
                entities.append(Obstacle(f"obstacle_{i}", ox, oy))

            return entities

        raise GenerationFailedError(
            f"ProceduralGenerator failed to find a valid layout after "
            f"{_MAX_RETRIES} attempts. "
            f"seed={seed}, grid={cfg.grid_width}x{cfg.grid_height}, "
            f"num_obstacles={cfg.num_obstacles}, "
            f"min_separation={cfg.min_separation}"
        )
