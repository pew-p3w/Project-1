# Emergent Communication in Asymmetric Dec-POMDPs

Research project investigating emergent communication protocols for coordinated target capture between two agents operating under strictly asymmetric observability and actuation constraints.

## Overview

Two agents — an Observer (Agent A) and an Actor (Agent B) — must cooperate to capture a target on a 64×64 discrete grid. Agent A sees everything but cannot move. Agent B is completely blind but can move in 8 directions. Coordination happens through a continuous message channel with artificial network latency.

Formally defined as an asymmetric Dec-POMDP: `⟨I, S, A, Z, T, O, R, γ⟩`

## Project Structure

```
├── Agent_A/          # Agent A policy and network code
├── Agent_B/          # Agent B policy and network code
├── Config/           # JSON configuration files
│   └── config.json   # Environment parameters
├── env/              # Grid environment (simulation layer)
│   ├── entity.py     # Base Entity dataclass
│   ├── objects.py    # AgentA, AgentB, Obstacle, Target
│   ├── config_loader.py
│   ├── errors.py
│   └── tests/        # Unit and property-based tests
├── jobs/             # Training and experiment job scripts
├── output/           # Results, logs, checkpoints
├── Resources/        # Reference materials
├── Tasks/            # Task planning documents
└── utils/            # Shared utilities
```

## Environment

The simulation layer (`env/`) is fully decoupled from any learning algorithm. All parameters are loaded from `Config/config.json` at initialization.

### Config Parameters

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `grid_width` | int | yes | — | Grid width |
| `grid_height` | int | yes | — | Grid height |
| `num_obstacles` | int | yes | — | Number of obstacles |
| `random_seed` | int | yes | — | Seed for reproducibility |
| `max_steps` | int | yes | — | Max steps per episode |
| `tau` | int | yes | — | Message latency (timesteps) |
| `min_separation` | int | no | 0 | Min distance between Agent B and target at spawn |
| `message_dim` | int | no | 16 | Message vector dimension |
| `debug` | bool | no | false | Enable text-grid renderer |
| `log_level` | str | no | "INFO" | Logging verbosity |

### Agents

- **Agent A (Observer):** Receives full state `z_A = s`. Sends a continuous message vector `m_t ∈ ℝ¹⁶` each timestep. No movement.
- **Agent B (Actor):** Receives no environment state `z_B = ∅`. Moves 8-directionally based solely on delayed messages from Agent A.

### Communication

Agent A transmits `m_t ∈ ℝ¹⁶` each timestep. Messages are delayed by `τ` timesteps via a FIFO latency buffer before delivery to Agent B. Early-episode steps (before the buffer fills) receive a zero vector.

## Running Tests

```bash
# Install dependencies
pip install pytest hypothesis

# Run all tests
pytest env/tests/

# Run property-based tests only
pytest env/tests/properties/
```

## Status

| Component | Status |
|---|---|
| Config loader | ✅ Complete |
| Entity hierarchy | ✅ Complete |
| Spatial index | 🔲 Pending |
| Latency buffer | 🔲 Pending |
| Procedural generator | 🔲 Pending |
| Movement system | 🔲 Pending |
| Observation interface | 🔲 Pending |
| Communication interface | 🔲 Pending |
| Reward & termination | 🔲 Pending |
| Full step pipeline | 🔲 Pending |
| Reset mechanism | 🔲 Pending |
| Debug & logging | 🔲 Pending |
