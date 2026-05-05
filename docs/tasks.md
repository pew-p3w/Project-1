# Implementation Plan: Multi-Agent Target Capture

## Overview

Incremental implementation of the Multi-Agent Target Capture environment using PettingZoo, Pymunk, and Stable Baselines3.

## Tasks

### Phase 1: Core Physics and Entities
- [x] Integrate `pymunk` space and body management.
- [x] Implement `Catcher` and `Target` entities with continuous movement.
- [x] Implement geometric obstacles (rect, circle, polygon).
- [ ] Implement moving target evasion logic.

### Phase 2: Perception and Communication
- [ ] Implement Ray-Casting observation engine.
- [ ] Implement object detection and distance calculation within rays.

### Phase 3: PettingZoo Integration
- [ ] Wrap core environment in PettingZoo `ParallelEnv` interface.
- [ ] Define `observation_space` and `action_space` using Gymnasium.
- [ ] Implement `step`, `reset`, and `render` methods.
- [ ] Add support for `AECEnv` wrappers.

### Phase 4: Reinforcement Learning (SB3)
- [ ] Set up training pipeline with Stable Baselines3.
- [ ] Implement multi-agent training wrappers for SB3 (e.g., Supersuit).
- [ ] Train baseline policies for coordinated capture.
- [ ] Evaluate performance against various target strategies and latencies.

### Phase 5: Visualization and Documentation
- [x] Update documentation (README, Design, Requirements).
- [ ] Enhace Pygame renderer with ray-cast visualization and capture effects.
- [ ] Create demo scripts for trained policies.

## Current Focus
- Transitioning environment core to PettingZoo interface.
- Implementing ray-casting observation logic.
