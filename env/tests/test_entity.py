"""Unit tests for the entity hierarchy (Task 2).

Covers:
- isinstance checks for all concrete types
- static/collidable flag defaults
- AgentB velocity field defaults
- Obstacle shape_def field
- Entity id/x/y types
- Equality and hashing based on id only
"""

import pytest

from env.entity import Entity
from env.objects import AgentA, AgentB, CircleDef, Obstacle, PolygonDef, RectDef, Target


# ---------------------------------------------------------------------------
# isinstance checks
# ---------------------------------------------------------------------------

def test_agent_a_is_entity():
    assert isinstance(AgentA("a1", 1.0, 2.0), Entity)


def test_agent_b_is_entity():
    assert isinstance(AgentB("b1", 3.0, 4.0), Entity)


def test_obstacle_is_entity():
    assert isinstance(Obstacle("o1", 5.0, 6.0), Entity)


def test_target_is_entity():
    assert isinstance(Target("t1", 7.0, 8.0), Entity)


# ---------------------------------------------------------------------------
# Flag defaults
# ---------------------------------------------------------------------------

def test_agent_a_flags():
    a = AgentA("a1", 0.0, 0.0)
    assert a.static is True
    assert a.collidable is False


def test_agent_b_flags():
    b = AgentB("b1", 0.0, 0.0)
    assert b.static is False
    assert b.collidable is True


def test_obstacle_flags():
    o = Obstacle("o1", 0.0, 0.0)
    assert o.static is True
    assert o.collidable is True


def test_target_flags():
    t = Target("t1", 0.0, 0.0)
    assert t.static is True
    assert t.collidable is False


# ---------------------------------------------------------------------------
# AgentB velocity field defaults
# ---------------------------------------------------------------------------

def test_agent_b_default_heading():
    b = AgentB("b1", 0.0, 0.0)
    assert b.heading == 0.0


def test_agent_b_default_speed():
    b = AgentB("b1", 0.0, 0.0)
    assert b.speed == 0.0


def test_agent_b_default_vx():
    b = AgentB("b1", 0.0, 0.0)
    assert b.vx == 0.0


def test_agent_b_default_vy():
    b = AgentB("b1", 0.0, 0.0)
    assert b.vy == 0.0


def test_agent_b_custom_fields():
    b = AgentB("b1", 1.0, 2.0, heading=1.5, speed=10.0, vx=3.0, vy=4.0)
    assert b.heading == 1.5
    assert b.speed == 10.0
    assert b.vx == 3.0
    assert b.vy == 4.0


# ---------------------------------------------------------------------------
# Obstacle shape_def field
# ---------------------------------------------------------------------------

def test_obstacle_shape_def_none_by_default():
    o = Obstacle("o1", 0.0, 0.0)
    assert o.shape_def is None


def test_obstacle_shape_def_rect():
    rd = RectDef(cx=10.0, cy=20.0, width=5.0, height=3.0, angle=0.0)
    o = Obstacle("o1", 10.0, 20.0, shape_def=rd)
    assert isinstance(o.shape_def, RectDef)
    assert o.shape_def.width == 5.0


def test_obstacle_shape_def_circle():
    cd = CircleDef(cx=50.0, cy=50.0, radius=15.0)
    o = Obstacle("o2", 50.0, 50.0, shape_def=cd)
    assert isinstance(o.shape_def, CircleDef)
    assert o.shape_def.radius == 15.0


def test_obstacle_shape_def_polygon():
    pd = PolygonDef(vertices=[(0.0, 0.0), (10.0, 0.0), (5.0, 8.0)])
    o = Obstacle("o3", 5.0, 3.0, shape_def=pd)
    assert isinstance(o.shape_def, PolygonDef)
    assert len(o.shape_def.vertices) == 3


# ---------------------------------------------------------------------------
# Entity id, x, y types
# ---------------------------------------------------------------------------

def test_entity_id_is_str():
    a = AgentA("agent_a", 1.0, 2.0)
    assert isinstance(a.id, str)


def test_entity_x_is_float():
    a = AgentA("a", 3.0, 4.0)
    assert isinstance(a.x, float)


def test_entity_y_is_float():
    a = AgentA("a", 3.0, 4.0)
    assert isinstance(a.y, float)


# ---------------------------------------------------------------------------
# Equality and hashing based on id only
# ---------------------------------------------------------------------------

def test_same_id_equal():
    a = AgentA("shared_id", 0.0, 0.0)
    b = AgentB("shared_id", 99.0, 99.0)
    assert a == b


def test_different_id_not_equal():
    a = AgentA("id_1", 0.0, 0.0)
    b = AgentA("id_2", 0.0, 0.0)
    assert a != b


def test_same_id_same_hash():
    a = AgentA("shared_id", 0.0, 0.0)
    b = Target("shared_id", 5.0, 5.0)
    assert hash(a) == hash(b)


def test_entities_usable_in_set():
    a = AgentA("a", 0.0, 0.0)
    b = AgentB("b", 1.0, 1.0)
    t = Target("t", 2.0, 2.0)
    s = {a, b, t}
    assert len(s) == 3


def test_position_update_does_not_break_equality():
    """Entities stay equal after position mutation (hash/eq based on id)."""
    b1 = AgentB("b1", 0.0, 0.0)
    b2 = AgentB("b1", 0.0, 0.0)
    b2.x = 100.0
    b2.y = 200.0
    assert b1 == b2
    assert hash(b1) == hash(b2)
