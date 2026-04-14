# Agent A — Observer

Agent A is the Observer in the asymmetric Dec-POMDP. It is stationary and has full, unoccluded visibility of the continuous 2D environment. Its sole role is to encode that state into a continuous message vector and transmit it to Agent B each timestep.

## Role

- Stationary — no movement action
- Receives full environment state `z_A = s` (positions, velocities, obstacle geometry)
- Sends a continuous message vector `m_t ∈ ℝ¹⁶` to Agent B each timestep

## Observability

Agent A sees everything in the continuous world:
- Its own position `(x, y)`
- Agent B's current position `(x, y)` and velocity `(vx, vy)`
- Target position `(x, y)`
- Full geometry of all obstacles (shape type + parameters)

## Communication

At each timestep `t`, Agent A produces a 16-dimensional float vector `m_t`. This message is passed to the environment's communication interface, which routes it through the latency buffer before delivery to Agent B after `τ` timesteps.

The key challenge: `m_t` must encode dense spatial abstractions of the continuous world — obstacle layout, Agent B's position relative to the target, optimal path — rather than collapsing into a trivial directional heuristic.

## Interface (Environment Side)

The environment accepts Agent A's message via `step(action_b, message_a)` where `message_a` is a `list[float]` of length 16. The environment validates the dimension and raises `MessageDimensionError` if incorrect.

## Observation Format

```python
obs_a = {
    "agent_a":          (x: float, y: float),
    "agent_b":          (x: float, y: float),
    "agent_b_velocity": (vx: float, vy: float),
    "target":           (x: float, y: float),
    "obstacles":        [{"type": str, ...shape_params}],
    "timestep":         int,
}
```

## Status

- [ ] Policy / network implementation (future spec)
- [ ] Training loop integration (future spec)
