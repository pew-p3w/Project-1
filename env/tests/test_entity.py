"""Unit tests for the entity hierarchy — isinstance checks and flag defaults."""

import pytest

from env.entity import Entity
from env.objects import AgentA, AgentB, Obstacle, Target


# ---------------------------------------------------------------------------
# isinstance checks
# ---------------------------------------------------------------------------

def test_agent_a_is_entity():
    assert isinstance(AgentA("a", 0, 0), Entity)


def test_agent_b_is_entity():
    assert isinstance(AgentB("b", 0, 0), Entity)


def test_obstacle_is_entity():
    assert isinstance(Obstacle("o", 0, 0), Entity)


def test_target_is_entity():
    assert isinstance(Target("t", 0, 0), Entity)


# ---------------------------------------------------------------------------
# Flag defaults
# ---------------------------------------------------------------------------

def test_agent_a_flags():
    e = AgentA("a1", 3, 7)
    assert e.static is False
    assert e.collidable is False


def test_agent_b_flags():
    e = AgentB("b1", 5, 5)
    assert e.static is False
    assert e.collidable is True


def test_obstacle_flags():
    e = Obstacle("obs1", 10, 20)
    assert e.static is True
    assert e.collidable is True


def test_target_flags():
    e = Target("tgt1", 63, 63)
    assert e.static is True
    assert e.collidable is False


# ---------------------------------------------------------------------------
# Position and id are stored correctly
# ---------------------------------------------------------------------------

def test_entity_fields_stored():
    e = AgentB("agent_b", 12, 34)
    assert e.id == "agent_b"
    assert e.x == 12
    assert e.y == 34
