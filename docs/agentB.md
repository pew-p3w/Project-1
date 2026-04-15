# Agent B — Actor

Agent B is the Actor in the asymmetric Dec-POMDP. It moves continuously through a 2D physics world and is completely blind to the environment state. It relies solely on delayed messages from Agent A to navigate toward the target.

## Role

- Receives no environment state: $\mathbf{z}_B = \emptyset$
- Moves continuously via velocity-based steering each timestep
- Must reach within `capture_radius` of the target to end the episode successfully

## Observability

Agent B sees nothing about the world. Its only input is the message `\mathbf{m}_{t-\tau}` delivered by the latency buffer — a 16-dimensional float vector sent by Agent A $\tau$ timesteps ago.

## Movement

Agent B moves like an ant or insect, smooth, continuous motion in any direction, physically blocked by obstacles and world boundaries.

### Physics

- Represented as a circular body with radius `agent_radius` in the pymunk physics engine
- Has a heading (angle in radians) and a scalar speed
- Velocity vector: `(vx, vy) = (speed × cos(heading), speed × sin(heading))`

### Action Space

Agent B's action is a continuous pair `(Δheading, Δspeed)`:

| Component | Type | Semantics | Clamping |
|---|---|---|---|
| `Δheading` | float (radians) | Change in heading direction | Clamped to `[−max_angular_velocity, +max_angular_velocity]` |
| `Δspeed` | float (world units/step) | Change in scalar speed | Result clamped to `[0, max_speed]` |

After clamping, the new velocity is applied to the physics body. pymunk handles collision response, if Agent B hits an obstacle or wall, it is deflected rather than passing through.

## Communication Latency

Messages from Agent A are delayed by $\tau$ timesteps. Agent B acts on stale information, which is the core challenge this project studies. Early-episode steps (before the buffer fills) receive a zero vector.

## Capture

An episode ends successfully when the Euclidean distance between Agent B and the Target is ≤ `capture_radius`. Agent B does not collide with the Target, it simply needs to get close enough.

## Interface (Environment Side)

Agent B's action is passed via `step(action_b, message_a)` where `action_b = (Δheading, Δspeed)`. The environment applies the steering update, advances the physics engine, and checks for capture.

## Status

- [ ] Policy / network implementation (future spec)
- [ ] Training loop integration (future spec)
