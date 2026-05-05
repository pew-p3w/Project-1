# Multi-Agent Coordination for Target Capture

A research project focused on emergent communication and coordination between two agents tasked with capturing a fast-moving target in a continuous 2D physics environment.

## Overview

Two agents must cooperate to catch a moving target within a strict time constraint. Both agents operate in a continuous 2D world powered by the `pymunk` physics engine. Unlike the previous asymmetric setup, both agents are now active participants with their own movement capabilities and observation spaces.

### Key Features

- **Multi-Agent Environment**: Built using the `PettingZoo` Parallel/AEC interface.
- **Ray-Casting Observations**: Agents perceive the world through rays, providing realistic, ego-centric partial observability.
- **Communication**: Agents can communicate via a dedicated channel to coordinate their strategy for catching a target that is faster than any individual agent.
- **Continuous Physics**: Realistic movement and collision handling using `pymunk`.
- **Reinforcement Learning**: Algorithms developed and trained using `Stable Baselines3`.

## Project Structure

```
├── Agent_A/          # Agent A policy and network code (SB3 compatible)
├── Agent_B/          # Agent B policy and network code (SB3 compatible)
├── Config/           # Configuration files
│   └── config.json   # Environment and training parameters
├── env/              # PettingZoo-compatible environment
│   ├── entity.py     # Base Entity dataclass
│   ├── objects.py    # Agent, Obstacle, Target definitions
│   ├── physics_engine.py  # Pymunk wrapper
│   ├── environment.py     # PettingZoo environment orchestrator
│   ├── renderer.py        # Pygame-based visualization
│   └── ...
├── docs/             # Technical documentation and design specs
├── tests/            # Unit and property-based tests
└── requirements.txt  # Project dependencies
```

## Technical Stack

- **Physics**: [Pymunk](http://www.pymunk.org/) (Chipmunk2D wrapper)
- **Interface**: [PettingZoo](https://pettingzoo.farama.org/) (MAv3)
- **Algorithms**: [Stable Baselines3](https://stable-baselines3.readthedocs.io/)
- **Visualisation**: [Pygame](https://www.pygame.org/)

## Getting Started

### Installation

```bash
pip install -r requirements.txt
```

### Running Tests

```bash
pytest tests/
```
