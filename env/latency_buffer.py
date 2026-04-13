"""Latency buffer implementing τ-step FIFO message delay."""

from collections import deque


class LatencyBuffer:
    """FIFO queue that delays messages by τ timesteps.

    When τ=0, push then pop returns the current message immediately.
    When τ>0, a message pushed at timestep t is returned at timestep t+τ.
    Before the buffer has received τ messages, pop returns a zero vector.
    """

    def __init__(self, tau: int, message_dim: int = 16) -> None:
        self._tau = tau
        self._message_dim = message_dim
        # Capacity is tau+1: holds tau delayed messages plus the current one
        self._queue: deque = deque(maxlen=tau + 1)

    def push(self, message: list[float]) -> None:
        """Add a message to the right end of the buffer."""
        self._queue.append(message)

    def pop(self) -> list[float]:
        """Return the oldest message, or a zero vector if buffer not yet full.

        The buffer is considered full when it contains tau+1 messages.
        Until then, early-episode pops return [0.0] * message_dim.
        """
        if len(self._queue) < self._tau + 1:
            return [0.0] * self._message_dim
        return self._queue.popleft()

    def clear(self) -> None:
        """Reset the buffer to its initial empty state."""
        self._queue.clear()
