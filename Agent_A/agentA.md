# Agent A — Observer

Agent A is the Observer in the asymmetric Dec-POMDP. It has full, unoccluded visibility of the environment state but cannot move. Its sole role is to encode that state into a continuous message vector and transmit it to Agent B each timestep.

## Role

- Receives full environment state `z_A = s` (positions of all entities: Agent B, Target, Obstacles)
- Sends a continuous message vector `m_t ∈ ℝ¹⁶` to Agent B each timestep
- Has no movement action — `𝒜_A` is the communication action only

## Observability

Agent A sees everything:
- Its own position
- Agent B's current position
- Target position
- All obstacle positions

## Communication

At each timestep `t`, Agent A produces a 16-dimensional float vector `m_t`. This message is passed to the environment's communication interface, which routes it through the latency buffer before delivery to Agent B.

The key challenge: `m_t` must encode dense spatial abstractions rather than collapsing into a trivial greedy directional heuristic. The emergent communication protocol is what this project investigates.

## Interface (Environment Side)

The environment accepts Agent A's message via `step(action_b, message_a)` where `message_a` is a `list[float]` of length 16. The environment validates the dimension and raises `MessageDimensionError` if incorrect.

## Status

- [ ] Policy / network implementation (future spec)
- [ ] Training loop integration (future spec)
