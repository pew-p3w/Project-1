"""Spatial index for O(1) average position-to-entity lookups."""

from env.entity import Entity


class SpatialIndex:
    """Maps grid positions to the set of entities occupying them.

    Backed by ``dict[tuple[int, int], set[Entity]]``.  All operations are
    O(1) average.  Empty-cell entries are removed automatically so the dict
    never accumulates stale keys.
    """

    def __init__(self) -> None:
        self._grid: dict[tuple[int, int], set[Entity]] = {}

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def add(self, entity: Entity) -> None:
        """Register *entity* at its current (x, y) position."""
        key = (entity.x, entity.y)
        if key not in self._grid:
            self._grid[key] = set()
        self._grid[key].add(entity)

    def remove(self, entity: Entity) -> None:
        """Deregister *entity* from its current (x, y) position.

        If the cell becomes empty the dict entry is deleted so the backing
        dict never grows unboundedly with stale keys.
        """
        key = (entity.x, entity.y)
        cell = self._grid.get(key)
        if cell is None:
            return
        cell.discard(entity)
        if not cell:
            del self._grid[key]

    def move(self, entity: Entity, new_x: int, new_y: int) -> None:
        """Atomically move *entity* from its current position to (new_x, new_y).

        After this call:
        - The old position does NOT contain *entity*.
        - The new position DOES contain *entity*.
        - ``entity.x`` and ``entity.y`` are updated to reflect the new position.
        """
        self.remove(entity)
        entity.x = new_x
        entity.y = new_y
        self.add(entity)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get(self, x: int, y: int) -> frozenset[Entity]:
        """Return an immutable snapshot of all entities at (x, y)."""
        cell = self._grid.get((x, y))
        if cell is None:
            return frozenset()
        return frozenset(cell)

    def has_collidable(self, x: int, y: int) -> bool:
        """Return True iff at least one collidable entity is at (x, y)."""
        cell = self._grid.get((x, y))
        if cell is None:
            return False
        return any(e.collidable for e in cell)
