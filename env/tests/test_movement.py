"""Unit tests for the movement system (env/actions.py).

Covers:
- All 8 action deltas produce correct candidate positions
- Valid move (open cell, in bounds) succeeds and agent position updates
- Move into obstacle is rejected, agent stays put
- Move out of bounds (all 4 edges + corners) is rejected, agent stays put
- Move onto Target position succeeds (Target is non-collidable)
- Move onto AgentA position succeeds (AgentA is non-collidable)
- apply_move returns True on success, False on rejection
"""

import pytest

from env.actions import (
    ACTION_DELTAS,
    ACTION_NAMES,
    apply_move,
    compute_candidate,
    is_valid_move,
)
from env.objects import AgentA, AgentB, Obstacle, Target
from env.spatial import SpatialIndex

GRID_W = 10
GRID_H = 10


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_spatial(*entities):
    """Build a SpatialIndex pre-populated with the given entities."""
    si = SpatialIndex()
    for e in entities:
        si.add(e)
    return si


# ---------------------------------------------------------------------------
# ACTION_DELTAS / ACTION_NAMES sanity
# ---------------------------------------------------------------------------

def test_action_deltas_has_eight_entries():
    assert len(ACTION_DELTAS) == 8


def test_action_names_has_eight_entries():
    assert len(ACTION_NAMES) == 8


# ---------------------------------------------------------------------------
# compute_candidate — all 8 directions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("action, dx, dy", [
    (0, 0, +1),   # N
    (1, +1, +1),  # NE
    (2, +1, 0),   # E
    (3, +1, -1),  # SE
    (4, 0, -1),   # S
    (5, -1, -1),  # SW
    (6, -1, 0),   # W
    (7, -1, +1),  # NW
])
def test_compute_candidate_all_actions(action, dx, dy):
    x, y = 5, 5
    cx, cy = compute_candidate(x, y, action)
    assert cx == x + dx
    assert cy == y + dy


# ---------------------------------------------------------------------------
# is_valid_move
# ---------------------------------------------------------------------------

def test_is_valid_move_open_cell():
    si = SpatialIndex()
    assert is_valid_move(5, 5, GRID_W, GRID_H, si) is True


def test_is_valid_move_blocked_by_obstacle():
    obs = Obstacle(id="obs1", x=5, y=5)
    si = make_spatial(obs)
    assert is_valid_move(5, 5, GRID_W, GRID_H, si) is False


def test_is_valid_move_out_of_bounds_negative_x():
    si = SpatialIndex()
    assert is_valid_move(-1, 5, GRID_W, GRID_H, si) is False


def test_is_valid_move_out_of_bounds_negative_y():
    si = SpatialIndex()
    assert is_valid_move(5, -1, GRID_W, GRID_H, si) is False


def test_is_valid_move_out_of_bounds_x_equals_width():
    si = SpatialIndex()
    assert is_valid_move(GRID_W, 5, GRID_W, GRID_H, si) is False


def test_is_valid_move_out_of_bounds_y_equals_height():
    si = SpatialIndex()
    assert is_valid_move(5, GRID_H, GRID_W, GRID_H, si) is False


def test_is_valid_move_non_collidable_target_allowed():
    target = Target(id="t1", x=5, y=5)
    si = make_spatial(target)
    assert is_valid_move(5, 5, GRID_W, GRID_H, si) is True


def test_is_valid_move_non_collidable_agent_a_allowed():
    agent_a = AgentA(id="a1", x=5, y=5)
    si = make_spatial(agent_a)
    assert is_valid_move(5, 5, GRID_W, GRID_H, si) is True


# ---------------------------------------------------------------------------
# apply_move — success cases
# ---------------------------------------------------------------------------

def test_apply_move_open_cell_returns_true():
    agent_b = AgentB(id="b1", x=5, y=5)
    si = make_spatial(agent_b)
    result = apply_move(agent_b, 0, GRID_W, GRID_H, si)  # N -> (5, 6)
    assert result is True


def test_apply_move_open_cell_updates_position():
    agent_b = AgentB(id="b1", x=5, y=5)
    si = make_spatial(agent_b)
    apply_move(agent_b, 0, GRID_W, GRID_H, si)  # N -> (5, 6)
    assert agent_b.x == 5
    assert agent_b.y == 6


def test_apply_move_updates_spatial_index():
    agent_b = AgentB(id="b1", x=5, y=5)
    si = make_spatial(agent_b)
    apply_move(agent_b, 2, GRID_W, GRID_H, si)  # E -> (6, 5)
    assert agent_b in si.get(6, 5)
    assert agent_b not in si.get(5, 5)


def test_apply_move_onto_target_succeeds():
    agent_b = AgentB(id="b1", x=4, y=5)
    target = Target(id="t1", x=5, y=5)
    si = make_spatial(agent_b, target)
    result = apply_move(agent_b, 2, GRID_W, GRID_H, si)  # E -> (5, 5)
    assert result is True
    assert agent_b.x == 5
    assert agent_b.y == 5


def test_apply_move_onto_agent_a_succeeds():
    agent_b = AgentB(id="b1", x=4, y=5)
    agent_a = AgentA(id="a1", x=5, y=5)
    si = make_spatial(agent_b, agent_a)
    result = apply_move(agent_b, 2, GRID_W, GRID_H, si)  # E -> (5, 5)
    assert result is True
    assert agent_b.x == 5
    assert agent_b.y == 5


# ---------------------------------------------------------------------------
# apply_move — rejection cases
# ---------------------------------------------------------------------------

def test_apply_move_into_obstacle_returns_false():
    agent_b = AgentB(id="b1", x=4, y=5)
    obs = Obstacle(id="obs1", x=5, y=5)
    si = make_spatial(agent_b, obs)
    result = apply_move(agent_b, 2, GRID_W, GRID_H, si)  # E -> (5, 5) blocked
    assert result is False


def test_apply_move_into_obstacle_agent_stays_put():
    agent_b = AgentB(id="b1", x=4, y=5)
    obs = Obstacle(id="obs1", x=5, y=5)
    si = make_spatial(agent_b, obs)
    apply_move(agent_b, 2, GRID_W, GRID_H, si)
    assert agent_b.x == 4
    assert agent_b.y == 5


# ---------------------------------------------------------------------------
# Boundary rejection — all 4 edges
# ---------------------------------------------------------------------------

def test_apply_move_out_of_bounds_west_edge():
    """Agent at x=0 moving W should be rejected."""
    agent_b = AgentB(id="b1", x=0, y=5)
    si = make_spatial(agent_b)
    result = apply_move(agent_b, 6, GRID_W, GRID_H, si)  # W -> (-1, 5)
    assert result is False
    assert agent_b.x == 0
    assert agent_b.y == 5


def test_apply_move_out_of_bounds_east_edge():
    """Agent at x=GRID_W-1 moving E should be rejected."""
    agent_b = AgentB(id="b1", x=GRID_W - 1, y=5)
    si = make_spatial(agent_b)
    result = apply_move(agent_b, 2, GRID_W, GRID_H, si)  # E -> (GRID_W, 5)
    assert result is False
    assert agent_b.x == GRID_W - 1


def test_apply_move_out_of_bounds_south_edge():
    """Agent at y=0 moving S should be rejected."""
    agent_b = AgentB(id="b1", x=5, y=0)
    si = make_spatial(agent_b)
    result = apply_move(agent_b, 4, GRID_W, GRID_H, si)  # S -> (5, -1)
    assert result is False
    assert agent_b.y == 0


def test_apply_move_out_of_bounds_north_edge():
    """Agent at y=GRID_H-1 moving N should be rejected."""
    agent_b = AgentB(id="b1", x=5, y=GRID_H - 1)
    si = make_spatial(agent_b)
    result = apply_move(agent_b, 0, GRID_W, GRID_H, si)  # N -> (5, GRID_H)
    assert result is False
    assert agent_b.y == GRID_H - 1


# ---------------------------------------------------------------------------
# Boundary rejection — corners
# ---------------------------------------------------------------------------

def test_apply_move_out_of_bounds_sw_corner():
    """Agent at (0, 0) moving SW should be rejected."""
    agent_b = AgentB(id="b1", x=0, y=0)
    si = make_spatial(agent_b)
    result = apply_move(agent_b, 5, GRID_W, GRID_H, si)  # SW -> (-1, -1)
    assert result is False
    assert (agent_b.x, agent_b.y) == (0, 0)


def test_apply_move_out_of_bounds_ne_corner():
    """Agent at (GRID_W-1, GRID_H-1) moving NE should be rejected."""
    agent_b = AgentB(id="b1", x=GRID_W - 1, y=GRID_H - 1)
    si = make_spatial(agent_b)
    result = apply_move(agent_b, 1, GRID_W, GRID_H, si)  # NE -> (GRID_W, GRID_H)
    assert result is False
    assert (agent_b.x, agent_b.y) == (GRID_W - 1, GRID_H - 1)


def test_apply_move_out_of_bounds_nw_corner():
    """Agent at (0, GRID_H-1) moving NW should be rejected."""
    agent_b = AgentB(id="b1", x=0, y=GRID_H - 1)
    si = make_spatial(agent_b)
    result = apply_move(agent_b, 7, GRID_W, GRID_H, si)  # NW -> (-1, GRID_H)
    assert result is False
    assert (agent_b.x, agent_b.y) == (0, GRID_H - 1)


def test_apply_move_out_of_bounds_se_corner():
    """Agent at (GRID_W-1, 0) moving SE should be rejected."""
    agent_b = AgentB(id="b1", x=GRID_W - 1, y=0)
    si = make_spatial(agent_b)
    result = apply_move(agent_b, 3, GRID_W, GRID_H, si)  # SE -> (GRID_W, -1)
    assert result is False
    assert (agent_b.x, agent_b.y) == (GRID_W - 1, 0)
