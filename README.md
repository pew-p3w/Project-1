# Emergent Communication in Asymmetric Dec-POMDPs

Research project investigating emergent communication protocols for coordinated target capture between two agents operating under strictly asymmetric observability and actuation constraints in a continuous 2D physics environment.

## Overview

Two agents — an Observer (Agent A) and an Actor (Agent B) — must cooperate to capture a target in a continuous 2D world. Agent A sees everything but cannot move. Agent B is completely blind but moves fluidly through the environment like an insect, physically blocked by geometric obstacles. Coordination happens through a continuous message channel with artificial network latency.

Formally defined as an asymmetric Dec-POMDP: `⟨I, S, A, Z, T, O, R, γ⟩`

## Project Structure

```
├── Agent_A/          # Agent A policy and network code
├── Agent_B/          # Agent B policy and network code
├── Config/           # JSON configuration files
│   └── config.json   # Environment parameters
├── env/              # Continuous physics environment (simulation layer)
│   ├── entity.py     # Base Entity dataclass (float positions)
│   ├── objects.py    # AgentA, AgentB, Obstacle, Target + shape defs
│   ├── physics_engine.py  # pymunk wrapper
│   ├── procedural_gen.py  # Seeded entity placement
│   ├── latency_buffer.py  # τ-step FIFO message delay
│   ├── environment.py     # DecPOMDPEnvironment orchestrator
│   ├── renderer.py        # Optional Pygame visualisation
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

The simulation layer (`env/`) is a continuous 2D physics world built on pymunk. It is fully decoupled from any learning algorithm. All parameters are loaded from `Config/config.json` at initialization.

### How It Works

- **World**: A continuous 2D space of configurable dimensions (e.g. 800×600 units)
- **Agent B** moves like an ant — smooth velocity-based steering, physically blocked by obstacles and walls
- **Agent A** is stationary, observes the full world state, sends a 16-float message each timestep
- **Obstacles** are geometric shapes: rectangular walls, circular pillars, convex polygons
- **Capture**: Agent B wins when it gets within `capture_radius` of the Target

### Agents

- **Agent A (Observer):** Receives full state `z_A = s`. Sends `m_t ∈ ℝ¹⁶` each timestep. No movement.
- **Agent B (Actor):** Receives no environment state `z_B = ∅`. Steers via `(Δheading, Δspeed)` actions based solely on delayed messages from Agent A.

### Communication

Agent A transmits `m_t ∈ ℝ¹⁶` each timestep. Messages are delayed by `τ` timesteps via a FIFO latency buffer before delivery to Agent B. Early-episode steps receive a zero vector.

### Config Parameters

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `world_width` | float | yes | — | World width in units |
| `world_height` | float | yes | — | World height in units |
| `agent_radius` | float | yes | — | Agent B collision radius |
| `max_speed` | float | yes | — | Max Agent B speed |
| `max_angular_velocity` | float | yes | — | Max heading change per step (radians) |
| `capture_radius` | float | yes | — | Distance threshold for capture |
| `random_seed` | int | yes | — | Seed for reproducibility |
| `max_steps` | int | yes | — | Max steps per episode |
| `tau` | int | yes | — | Message latency (timesteps) |
| `min_separation` | float | no | 0.0 | Min spawn distance between Agent B and target |
| `obstacles` | list | no | [] | Explicit obstacle definitions |
| `render` | bool | no | false | Enable Pygame window |
| `log_level` | str | no | "INFO" | Logging verbosity |

### Obstacle Types

```json
{"type": "rect",    "cx": 200.0, "cy": 300.0, "width": 60.0, "height": 20.0, "angle": 0.0}
{"type": "circle",  "cx": 500.0, "cy": 200.0, "radius": 30.0}
{"type": "polygon", "vertices": [[400,100],[450,150],[380,160]]}
```

## Running Tests

```bash
# Install dependencies
pip install pytest hypothesis pymunk pygame

# Run all tests
pytest env/tests/

# Run property-based tests only
pytest env/tests/properties/
```

## Status

| Component | Status |
|---|---|
| Config loader | 🔄 Needs update (new params) |
| Entity hierarchy | 🔄 Needs update (float coords, shape defs) |
| Physics engine (pymunk) | 🔲 Pending |
| Procedural generator | 🔄 Needs update (continuous coords) |
| Latency buffer | ✅ Complete |
| Velocity-based movement | 🔲 Pending |
| Observation interface | 🔄 Needs update |
| Communication interface | 🔲 Pending |
| Reward & termination | 🔲 Pending |
| Full step pipeline | 🔲 Pending |
| Reset mechanism | 🔲 Pending |
| Pygame renderer | 🔲 Pending |
| Debug & logging | 🔲 Pending |
