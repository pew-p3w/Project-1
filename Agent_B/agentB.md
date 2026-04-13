# Agent B — Actor

Agent B is the Actor in the asymmetric Dec-POMDP. It is completely blind to the environment state and relies solely on delayed messages from Agent A to navigate toward the target.

## Role

- Receives no environment state: `z_B = ∅`
- Moves 8-directionally each timestep based solely on the message delivered by the latency buffer
- Must capture the target to end the episode successfully

## Observability

Agent B sees nothing about the world. Its only input is the message `m_{t-τ}` delivered by the latency buffer — a 16-dimensional float vector that was sent by Agent A `τ` timesteps ago.

## Action Space

8 discrete actions (cardinal + diagonal):

| Index | Direction | (Δx, Δy) |
|---|---|---|
| 0 | N  | (0, +1)  |
| 1 | NE | (+1, +1) |
| 2 | E  | (+1, 0)  |
| 3 | SE | (+1, -1) |
| 4 | S  | (0, -1)  |
| 5 | SW | (-1, -1) |
| 6 | W  | (-1, 0)  |
| 7 | NW | (-1, +1) |

Invalid moves (out of bounds or into an obstacle) are silently rejected — Agent B stays in place.

## Communication Latency

Messages from Agent A are delayed by `τ` timesteps. Agent B acts on stale information, which is the core challenge this project studies. Early-episode steps (before the buffer fills) receive a zero vector.

## Interface (Environment Side)

Agent B's action is passed via `step(action_b, message_a)` where `action_b ∈ {0..7}`. The environment applies movement, checks bounds and collisions, and updates the spatial index.

## Status

- [ ] Policy / network implementation (future spec)
- [ ] Training loop integration (future spec)
