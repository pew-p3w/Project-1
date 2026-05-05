# Requirements Document: Multi-Agent Target Capture

## Introduction

This document specifies the requirements for the continuous physics-based environment for a Multi-Agent Target Capture research project. The system simulates two active catcher agents that must coordinate via communication to capture a fast-moving target. The environment implements continuous 2D physics using `pymunk`, exposes a `PettingZoo` interface, and is designed for use with `Stable Baselines3`.

---

## Glossary

- **Environment**: The simulation system managing the world, entities, physics, and PettingZoo interface.
- **Catcher Agent**: One of two active agents tasked with capturing the target. Both move and communicate.
- **Target**: A dynamic entity that actively evades catchers.
- **Ray-Casting**: The observation mechanism where agents project rays to perceive their surroundings.
- **PettingZoo**: The multi-agent environment standard used for the project interface.
- **Pymunk**: The 2D physics engine used for simulation.
- **Capture**: Occurs when a catcher is within `capture_radius` of the target.

---

## High-Level Requirements

### Requirement 1: PettingZoo Interface
1. The environment SHALL implement the PettingZoo `ParallelEnv` interface.
2. The environment SHALL support the `AECEnv` interface via the `parallel_to_aec` wrapper if necessary.
3. The environment SHALL define `action_spaces` and `observation_spaces` for all agents.

### Requirement 2: Continuous Physics
1. The physics simulation SHALL be powered by `pymunk`.
2. Catchers and the Target SHALL be represented as circular bodies with radius and mass.
3. Movement SHALL be velocity-based or force-based, as configured.
4. Collisions SHALL be resolved by `pymunk`, preventing entities from passing through obstacles or each other (except for capture detection).

### Requirement 3: Ray-Casting Observations
1. Each agent SHALL receive an observation consisting of ray-cast data.
2. Rays SHALL detect distance to and type of the nearest object (Agent, Target, Obstacle, Wall).
3. The number of rays, range, and field of view SHALL be configurable.

### Requirement 4: Dynamic Target Behavior
1. The Target SHALL be capable of movement.
2. The Target SHALL follow an evasion strategy to avoid capture.
3. The Target's speed SHALL be configurable, typically faster than individual catchers.

### Requirement 6: Reward Structure
1. The environment SHALL provide a reward signal that encourages cooperation and fast capture.
2. A large positive reward SHALL be given upon successful capture.
3. Shaped rewards (e.g., distance-based) and time penalties SHALL be supported.

---

## Technical Specifications

### Physics Integration
- Timestep: Constant (e.g., 1/60s).
- Collision Filtering: Different categories for agents, targets, and obstacles to manage interactions.

### Observation Space (per Agent)
- `ray_data`: `Box(low=0, high=1, shape=(num_rays, 2))` representing distance and one-hot encoded type.
- `internal_state`: `Box(...)` for velocity and last action.
- `received_message`: `Box(low=-inf, high=inf, shape=(message_dim,))`.

### Action Space (per Agent)
- `movement`: `Box(low=-1, high=1, shape=(2,))` for thrust/steering.
- `message_out`: `Box(low=-inf, high=inf, shape=(message_dim,))`.
