"""Unit tests for SpatialIndex (env/spatial.py)."""

import pytest

from env.entity import Entity
from env.objects import AgentA, AgentB, Obstacle, Target
from env.spatial import SpatialIndex


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_entity(id: str, x: int, y: int, collidable: bool) -> Entity:
    return Entity(id=id, x=x, y=y, static=False, collidable=collidable)


# ---------------------------------------------------------------------------
# add / get
# ---------------------------------------------------------------------------

class TestAdd:
    def test_add_entity_then_get_returns_it(self):
        idx = SpatialIndex()
        e = make_entity("e1", 3, 5, collidable=False)
        idx.add(e)
        assert e in idx.get(3, 5)

    def test_get_empty_position_returns_empty_frozenset(self):
        idx = SpatialIndex()
        result = idx.get(0, 0)
        assert result == frozenset()

    def test_get_returns_frozenset(self):
        idx = SpatialIndex()
        e = make_entity("e1", 1, 1, collidable=False)
        idx.add(e)
        assert isinstance(idx.get(1, 1), frozenset)

    def test_multiple_entities_at_same_position(self):
        idx = SpatialIndex()
        e1 = make_entity("e1", 2, 2, collidable=False)
        e2 = make_entity("e2", 2, 2, collidable=True)
        idx.add(e1)
        idx.add(e2)
        result = idx.get(2, 2)
        assert e1 in result
        assert e2 in result
        assert len(result) == 2

    def test_add_does_not_affect_other_positions(self):
        idx = SpatialIndex()
        e = make_entity("e1", 4, 4, collidable=False)
        idx.add(e)
        assert idx.get(4, 5) == frozenset()
        assert idx.get(5, 4) == frozenset()


# ---------------------------------------------------------------------------
# remove
# ---------------------------------------------------------------------------

class TestRemove:
    def test_remove_entity_no_longer_in_get(self):
        idx = SpatialIndex()
        e = make_entity("e1", 1, 1, collidable=False)
        idx.add(e)
        idx.remove(e)
        assert e not in idx.get(1, 1)

    def test_remove_cleans_up_empty_cell(self):
        """Removing the last entity from a cell should delete the dict entry."""
        idx = SpatialIndex()
        e = make_entity("e1", 7, 7, collidable=False)
        idx.add(e)
        idx.remove(e)
        # get on that position should still return empty frozenset (no KeyError)
        assert idx.get(7, 7) == frozenset()

    def test_remove_only_removes_target_entity(self):
        idx = SpatialIndex()
        e1 = make_entity("e1", 3, 3, collidable=False)
        e2 = make_entity("e2", 3, 3, collidable=True)
        idx.add(e1)
        idx.add(e2)
        idx.remove(e1)
        result = idx.get(3, 3)
        assert e1 not in result
        assert e2 in result

    def test_remove_nonexistent_entity_does_not_raise(self):
        idx = SpatialIndex()
        e = make_entity("e1", 0, 0, collidable=False)
        # Never added — should not raise
        idx.remove(e)


# ---------------------------------------------------------------------------
# move
# ---------------------------------------------------------------------------

class TestMove:
    def test_move_old_position_cleared(self):
        idx = SpatialIndex()
        e = make_entity("e1", 0, 0, collidable=False)
        idx.add(e)
        idx.move(e, 5, 5)
        assert e not in idx.get(0, 0)

    def test_move_new_position_has_entity(self):
        idx = SpatialIndex()
        e = make_entity("e1", 0, 0, collidable=False)
        idx.add(e)
        idx.move(e, 5, 5)
        assert e in idx.get(5, 5)

    def test_move_updates_entity_coordinates(self):
        idx = SpatialIndex()
        e = make_entity("e1", 1, 2, collidable=False)
        idx.add(e)
        idx.move(e, 9, 8)
        assert e.x == 9
        assert e.y == 8

    def test_move_atomicity_old_empty_new_populated(self):
        """After move, old cell is empty and new cell contains entity."""
        idx = SpatialIndex()
        e = make_entity("e1", 0, 0, collidable=False)
        idx.add(e)
        idx.move(e, 3, 4)
        assert idx.get(0, 0) == frozenset()
        assert e in idx.get(3, 4)

    def test_move_to_same_position(self):
        """Moving to the same position should be a no-op."""
        idx = SpatialIndex()
        e = make_entity("e1", 2, 2, collidable=False)
        idx.add(e)
        idx.move(e, 2, 2)
        assert e in idx.get(2, 2)

    def test_move_does_not_disturb_other_entities_at_old_position(self):
        idx = SpatialIndex()
        e1 = make_entity("e1", 1, 1, collidable=False)
        e2 = make_entity("e2", 1, 1, collidable=True)
        idx.add(e1)
        idx.add(e2)
        idx.move(e1, 6, 6)
        assert e2 in idx.get(1, 1)
        assert e1 not in idx.get(1, 1)


# ---------------------------------------------------------------------------
# has_collidable
# ---------------------------------------------------------------------------

class TestHasCollidable:
    def test_true_when_collidable_entity_present(self):
        idx = SpatialIndex()
        e = make_entity("obs", 4, 4, collidable=True)
        idx.add(e)
        assert idx.has_collidable(4, 4) is True

    def test_false_when_only_non_collidable_present(self):
        idx = SpatialIndex()
        e = make_entity("target", 4, 4, collidable=False)
        idx.add(e)
        assert idx.has_collidable(4, 4) is False

    def test_false_for_empty_position(self):
        idx = SpatialIndex()
        assert idx.has_collidable(10, 10) is False

    def test_true_when_mixed_entities_include_collidable(self):
        idx = SpatialIndex()
        nc = make_entity("nc", 5, 5, collidable=False)
        c = make_entity("c", 5, 5, collidable=True)
        idx.add(nc)
        idx.add(c)
        assert idx.has_collidable(5, 5) is True

    def test_false_after_collidable_removed(self):
        idx = SpatialIndex()
        e = make_entity("obs", 3, 3, collidable=True)
        idx.add(e)
        idx.remove(e)
        assert idx.has_collidable(3, 3) is False


# ---------------------------------------------------------------------------
# Concrete entity types (objects.py)
# ---------------------------------------------------------------------------

class TestConcreteEntityTypes:
    def test_obstacle_is_collidable(self):
        idx = SpatialIndex()
        obs = Obstacle(id="o1", x=2, y=2)
        idx.add(obs)
        assert idx.has_collidable(2, 2) is True

    def test_target_is_not_collidable(self):
        idx = SpatialIndex()
        tgt = Target(id="t1", x=3, y=3)
        idx.add(tgt)
        assert idx.has_collidable(3, 3) is False

    def test_agent_b_is_collidable(self):
        idx = SpatialIndex()
        b = AgentB(id="b", x=1, y=1)
        idx.add(b)
        assert idx.has_collidable(1, 1) is True

    def test_agent_a_is_not_collidable(self):
        idx = SpatialIndex()
        a = AgentA(id="a", x=0, y=0)
        idx.add(a)
        assert idx.has_collidable(0, 0) is False
