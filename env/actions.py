"""Action space definitions and movement logic for Agent B."""

from env.objects import AgentB
from env.spatial import SpatialIndex

# 8-directional action space: action index -> (Δx, Δy)
ACTION_DELTAS: dict[int, tuple[int, int]] = {
    0: (0, +1),   # N
    1: (+1, +1),  # NE
    2: (+1, 0),   # E
    3: (+1, -1),  # SE
    4: (0, -1),   # S
    5: (-1, -1),  # SW
    6: (-1, 0),   # W
    7: (-1, +1),  # NW
}

# Human-readable direction names
ACTION_NAMES: dict[int, str] = {
    0: "N",
    1: "NE",
    2: "E",
    3: "SE",
    4: "S",
    5: "SW",
    6: "W",
    7: "NW",
}


def compute_candidate(x: int, y: int, action: int) -> tuple[int, int]:
    """Return the candidate position after applying the given action.

    Args:
        x: Current x-coordinate.
        y: Current y-coordinate.
        action: Action index in range [0, 7].

    Returns:
        (new_x, new_y) = (x + Δx, y + Δy)
    """
    dx, dy = ACTION_DELTAS[action]
    return (x + dx, y + dy)


def is_valid_move(
    candidate_x: int,
    candidate_y: int,
    grid_width: int,
    grid_height: int,
    spatial_index: SpatialIndex,
) -> bool:
    """Return True if the candidate position is in bounds and unobstructed.

    Args:
        candidate_x: Proposed x-coordinate.
        candidate_y: Proposed y-coordinate.
        grid_width: Width of the grid (valid x: 0 <= x < grid_width).
        grid_height: Height of the grid (valid y: 0 <= y < grid_height).
        spatial_index: Current spatial index for collision queries.

    Returns:
        True if the move is legal; False otherwise.
    """
    in_bounds = (0 <= candidate_x < grid_width) and (0 <= candidate_y < grid_height)
    if not in_bounds:
        return False
    return not spatial_index.has_collidable(candidate_x, candidate_y)


def apply_move(
    agent_b: AgentB,
    action: int,
    grid_width: int,
    grid_height: int,
    spatial_index: SpatialIndex,
) -> bool:
    """Apply a movement action to Agent B if valid; otherwise leave it in place.

    The spatial index is updated atomically on a successful move.

    Args:
        agent_b: The AgentB entity to move.
        action: Action index in range [0, 7].
        grid_width: Width of the grid.
        grid_height: Height of the grid.
        spatial_index: Spatial index to update on success.

    Returns:
        True if the agent moved; False if the move was rejected.
    """
    cx, cy = compute_candidate(agent_b.x, agent_b.y, action)
    if is_valid_move(cx, cy, grid_width, grid_height, spatial_index):
        spatial_index.move(agent_b, cx, cy)
        return True
    return False
