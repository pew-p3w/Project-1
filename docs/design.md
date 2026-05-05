# Design Document: Multi-Agent Target Capture Environment

## Overview

This document describes the technical design for the Multi-Agent Target Capture environment. The system simulates a continuous 2D world where two agents must cooperate to capture a fast-moving target via a communication channel.

The environment is designed to be compatible with the **PettingZoo** Parallel/AEC interface and is optimized for training with **Stable Baselines3**.

### Key Design Goals

- **Symmetry and Cooperation**: Both agents are active participants with movement and communication capabilities.
- **Realistic Perception**: Agents use ray-casting for observation, simulating limited field-of-view and occlusion.
- **Dynamic Challenge**: The target is faster than individual agents, necessitating coordinated pincer movements or strategy.
- **Continuous Physics**: Leverages `pymunk` for high-fidelity collision detection and response.
- **Modularity**: Separation between physics simulation, agent logic, and RL interfaces.

---

## Architecture

The environment follows the PettingZoo API structure, wrapping a core physics engine.


### Core Components

| Module | Responsibility |
|---|---|
| `environment.py` | Implements PettingZoo `ParallelEnv` / `AECEnv` interface. |
| `physics_engine.py` | Manages the Pymunk space, bodies, and collision callbacks. |
| `objects.py` | Definitions for `Agent`, `Target`, and `Obstacle` entities. |
| `ray_cast.py` | Logic for projecting rays from agents to generate observations. |

---

## Environment Specs

### Observation Space

Each agent receives a structured observation:
1. **Ray-casts**: A fixed number of rays (e.g., 32) cast in a 360-degree (or limited) arc. Each ray returns:
   - Distance to nearest object.
   - Type of object hit (Agent, Target, Obstacle, Wall).
2. **Internal State**:
   - Current velocity.
   - Previous action.
3. **Communication**:
   - Received message from the other agent.

### Action Space

Continuous action space for each agent:
1. **Movement**: `(force_x, force_y)` or `(thrust, steering)`.
2. **Communication**: A vector of floats (e.g., 8 dimensions) to be sent to the other agent.

### Reward Function

- **Global Reward**: Positive reward when the target is captured.
- **Distance Shaping**: Small negative reward proportional to distance from target to encourage pursuit.
- **Time Penalty**: Small negative reward per step to encourage fast capture.
- **Capture**: Occurs when an agent is within `capture_radius` of the target.

---

## Moving Target Logic

The target is not static. It follows a strategy to evade agents:
- **Evasion**: Moves away from the nearest agent.
- **Obstacle Avoidance**: Uses its own ray-casting to avoid getting stuck.
- **Speed**: Configurable to be faster than a single agent but slower than the combined theoretical speed/coverage of two agents.

---

## Communication Protocol

### Physics with Pymunk
- Fixed timestep integration for stability.
- Elastic collisions for agents and obstacles.
- Friction and damping to simulate realistic movement.

### Ray-Casting
- Uses Pymunk's `segment_query` to find intersections.
- Results are normalized to `[0, 1]` based on `max_ray_length`.

### PettingZoo Compatibility
- Supports both `aec` (sequential) and `parallel` (simultaneous) stepping.
- Uses `gymnasium` spaces for broad compatibility.
