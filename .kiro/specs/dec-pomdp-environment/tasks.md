# Implementation Plan: Dec-POMDP Environment

## Overview

Incremental implementation of the asymmetric Dec-POMDP grid environment in Python. Each task builds on the previous, ending with a fully wired environment ready for integration with learning algorithms. The design document and config schema are the authoritative references throughout.

## Tasks

- [x] 1. Project structure and configuration loader
  - Create the directory layout: `env/`, `env/tests/`, `env/tests/properties/`
  - Create `env/__init__.py`, `env/errors.py` with all custom exception classes (`ConfigValidationError`, `MessageDimensionError`, `EpisodeTerminatedError`, `BoundaryViolationError`, `GenerationFailedError`)
  - Implement `env/config_loader.py`: `EnvConfig` dataclass and `ConfigLoader.load(path)` that validates all required fields and raises `ConfigValidationError` naming the offending field
  - Create a sample `config.json` in the project root matching the JSON schema in the design
  - _Requirements: 1.1, 1.2, 1.3, 1.5_

  - [x]* 1.1 Write property test for config error naming (Property 1)
    - **Property 1: Config Error Names the Offending Field**
    - **Validates: Requirements 1.3**
    - Use `st.sampled_from(REQUIRED_FIELDS)` to generate missing/invalid fields; assert `ConfigValidationError` message contains the field name

- [x] 2. Entity hierarchy
  - Implement `env/entity.py`: abstract `Entity` dataclass with `id`, `x`, `y`, `static`, `collidable`
  - Implement `env/objects.py`: concrete classes `AgentA`, `AgentB`, `Obstacle`, `Target` with correct flag defaults per the design hierarchy table
  - Write `env/tests/test_entity.py`: `isinstance` checks and flag defaults for each concrete type
  - _Requirements: 3.1, 3.2, 3.4, 3.5_

- [x] 3. Spatial index
  - Implement `env/spatial.py`: `SpatialIndex` backed by `dict[tuple[int,int], set[Entity]]` with `add`, `remove`, `move` (atomic), `get`, `has_collidable`
  - Write `env/tests/test_spatial_index.py`: unit tests for add/remove/move/get/has_collidable
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 3.1 Write property test for spatial index round-trip (Property 4)
    - **Property 4: Spatial Index Round-Trip**
    - **Validates: Requirements 4.1**
    - Use `st.integers(0, 63)` for positions; assert add then get contains entity, remove then get does not

  - [ ]* 3.2 Write property test for spatial index move atomicity (Property 5)
    - **Property 5: Spatial Index Move Atomicity**
    - **Validates: Requirements 4.2**
    - Assert old position does not contain entity and new position does after `move()`

  - [ ]* 3.3 Write property test for collision correctness (Property 6)
    - **Property 6: Collision Correctness**
    - **Validates: Requirements 4.3, 4.4, 6.3, 6.4**
    - Assert `has_collidable()` iff at least one collidable entity is present; verify movement rejection/acceptance accordingly

- [x] 4. Latency buffer
  - Implement `env/latency_buffer.py`: `LatencyBuffer(tau, message_dim=16)` using `collections.deque`; implement `push` and `pop` with zero-vector fallback before buffer fills
  - Write `env/tests/test_latency_buffer.py`: unit tests for τ=0, τ=1, τ=3, early-episode zero vectors
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [ ]* 4.1 Write property test for latency buffer round-trip (Property 14)
    - **Property 14: Latency Buffer Round-Trip**
    - **Validates: Requirements 9.5, 10.2, 10.4, 10.5**
    - Use `st.lists(st.floats(allow_nan=False), min_size=16, max_size=16)` and `st.integers(0, 10)` for tau; push message, pop τ times discarding, final pop equals original message

  - [ ]* 4.2 Write property test for zero vector before buffer fills (Property 15)
    - **Property 15: Zero Vector Before Buffer Fills**
    - **Validates: Requirements 10.3**
    - Use `st.integers(1, 20)` for tau; assert first τ pops on fresh buffer all return `[0.0] * 16`

- [x] 5. Procedural generator
  - Implement `env/procedural_gen.py`: `ProceduralGenerator(config)` with `generate(seed) -> list[Entity]` using `random.Random(seed)` (not global state)
  - Enforce: no overlapping collidable entities, AgentB ≠ Target position, `min_separation` Manhattan distance check, all positions within grid bounds; retry on conflict up to a limit then raise `GenerationFailedError`
  - Write `env/tests/test_procedural_gen.py`: unit tests for overlap-free placement, seed reproducibility, min_separation
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 5.2, 5.3_

  - [ ]* 5.1 Write property test for reproducibility (Property 2)
    - **Property 2: Reproducibility — Same Seed Produces Identical Layout**
    - **Validates: Requirements 1.4, 7.2, 7.3, 13.4**
    - Use `st.integers()` for seeds; call `generate(seed)` twice, assert all entity positions are identical

  - [ ]* 5.2 Write property test for all entities within bounds after reset (Property 3)
    - **Property 3: All Entities Within Grid Bounds After Reset**
    - **Validates: Requirements 2.1, 5.2, 7.1**
    - Assert every entity satisfies `0 ≤ x < grid_width` and `0 ≤ y < grid_height`

  - [ ]* 5.3 Write property test for initialization non-overlap invariant (Property 8)
    - **Property 8: Initialization Non-Overlap Invariant**
    - **Validates: Requirements 5.3, 7.4**
    - Assert no two collidable entities share a position and AgentB position ≠ Target position

  - [ ]* 5.4 Write property test for minimum separation (Property 10)
    - **Property 10: Minimum Separation Enforced**
    - **Validates: Requirements 7.5**
    - Use configs with `min_separation > 0`; assert Manhattan distance between AgentB and Target ≥ min_separation

- [ ] 6. Checkpoint — core components complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Movement system
  - Define `ACTION_DELTAS` mapping in `env/objects.py` or a dedicated `env/actions.py` per the 8-direction table in the design
  - Implement movement validation logic (bounds check + `has_collidable`) as a helper in `env/environment.py` or `env/spatial.py`
  - Write `env/tests/test_movement.py`: unit tests for each of the 8 actions, boundary rejection, collision rejection
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ]* 7.1 Write property test for action translation correctness (Property 9)
    - **Property 9: Action Translation Correctness**
    - **Validates: Requirements 6.2**
    - Use `st.integers(0, 7)` for actions and `st.integers(0, 63)` for positions; assert candidate = start + delta

  - [ ]* 7.2 Write property test for boundary enforcement (Property 7)
    - **Property 7: Boundary Enforcement**
    - **Validates: Requirements 2.4, 5.1, 6.4**
    - Generate positions at or near grid edges with actions pointing out-of-bounds; assert AgentB position unchanged after step

- [-] 8. Observation interface
  - Implement `generate_observations()` in `env/environment.py` returning `ObsA` dict (agent_a, agent_b, target, obstacles sorted, timestep) and `ObsB = {}`
  - Write `env/tests/test_environment.py`: unit tests for `reset()` returning `(obs_a, obs_b)` tuple, obs_a key consistency across steps, obs_b always empty
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ]* 8.1 Write property test for Agent A observation completeness (Property 11)
    - **Property 11: Agent A Observation Completeness and Consistency**
    - **Validates: Requirements 8.1, 8.4**
    - Assert obs_a contains all entity positions and key set is identical at every timestep within an episode

  - [ ]* 8.2 Write property test for Agent B observation always empty (Property 12)
    - **Property 12: Agent B Observation Is Always Empty**
    - **Validates: Requirements 8.2**
    - Assert `obs_b == {}` for any environment state and any sequence of steps

- [ ] 9. Communication interface and message validation
  - Implement message acceptance and `MessageDimensionError` raising at the start of `step()` in `env/environment.py`
  - Wire `latency_buffer.push(message_a)` and `delayed_msg = latency_buffer.pop()` into the step pipeline; return `delayed_msg` in `info["message"]`
  - Write `env/tests/test_environment.py`: unit tests for valid 16-float message accepted, wrong-length message raises error
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 9.1 Write property test for message dimension validation (Property 13)
    - **Property 13: Message Dimension Validation**
    - **Validates: Requirements 9.1, 9.2**
    - Use `st.lists(st.floats())` of varying lengths; assert length-16 accepted, all others raise `MessageDimensionError`

- [ ] 10. Reward and termination logic
  - Implement `compute_reward_and_termination()` in `env/environment.py` per the design pseudocode (capture → +1/True, timeout → 0/True, ongoing → 0/False)
  - Implement `EpisodeTerminatedError` guard at `step()` entry
  - Write `env/tests/test_reward.py`: unit tests for capture, timeout, ongoing, and step-on-terminated
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 12.2_

  - [ ]* 10.1 Write property test for capture triggers reward and termination (Property 16)
    - **Property 16: Capture Triggers Positive Reward and Termination**
    - **Validates: Requirements 11.1, 11.2**
    - Move AgentB to Target position; assert `reward > 0` and `terminated == True`

  - [ ]* 10.2 Write property test for no-capture steps return zero reward (Property 17)
    - **Property 17: No-Capture Steps Return Zero Reward**
    - **Validates: Requirements 11.4**
    - Generate step sequences where AgentB never reaches Target; assert all steps return `reward == 0` and `terminated == False`

  - [ ]* 10.3 Write property test for timeout termination (Property 18)
    - **Property 18: Timeout Terminates with Zero Reward**
    - **Validates: Requirements 11.3**
    - Use configs with small `max_steps`; run exactly `max_steps` steps without capture; assert `terminated == True` and `reward == 0`

  - [ ]* 10.4 Write property test for step on terminated episode raises error (Property 19)
    - **Property 19: Step on Terminated Episode Raises Error**
    - **Validates: Requirements 11.5, 12.2**
    - After termination (capture or timeout), assert `step()` raises `EpisodeTerminatedError`

- [ ] 11. Full step pipeline and timestep counter
  - Wire the complete ordered step pipeline in `env/environment.py` per the design spec (validate → push → pop → move → timestep++ → reward → observations → return StepResult)
  - Implement `state_dict()` returning full current state as a structured dict
  - Write unit tests in `env/tests/test_environment.py` for pipeline ordering (mock-based) and `state_dict()` accuracy
  - _Requirements: 12.1, 12.3, 14.3_

  - [ ]* 11.1 Write property test for timestep increments by one per step (Property 20)
    - **Property 20: Timestep Increments by One Per Step**
    - **Validates: Requirements 12.3**
    - Use `st.integers(1, 100)` for step counts; assert `env.timestep == n` after n steps

  - [ ]* 11.2 Write property test for state dict accuracy (Property 22)
    - **Property 22: State Dict Reflects Current Entity Positions**
    - **Validates: Requirements 14.3**
    - Assert `state_dict()` positions match direct entity position queries for any state

- [ ] 12. Reset mechanism
  - Implement `reset(seed=None)` in `env/environment.py`: clear entities, reset timestep to 0, clear latency buffer, invoke procedural generator, return `(obs_a, obs_b)`
  - Support optional seed override per Requirements 13.4
  - Write unit tests for reset returning correct tuple, timestep=0, and buffer cleared
  - _Requirements: 13.1, 13.2, 13.3, 13.4_

  - [ ]* 12.1 Write property test for reset clears state (Property 21)
    - **Property 21: Reset Clears State**
    - **Validates: Requirements 13.1**
    - After mid-episode or terminated state, call `reset()`; assert `timestep == 0` and first 16 pops of a fresh buffer return zero vectors

- [ ] 13. Checkpoint — full environment wired
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 14. Logging and debug module
  - Implement configurable logging in `env/environment.py` using Python's `logging` module at levels controlled by `log_level` config field; log entity positions, movement outcomes, collision events
  - Implement `env/debug.py`: text-grid renderer that prints entity positions to stdout when `debug=True` in config
  - Write unit tests for debug renderer output format
  - _Requirements: 14.1, 14.2_

- [ ] 15. Extensibility wiring and final integration
  - Verify no hardcoded grid dimensions exist anywhere in environment logic (all from `EnvConfig`)
  - Add support for injecting an alternative `ProceduralGenerator` subclass via `DecPOMDPEnvironment.__init__` parameter
  - Write unit tests: custom entity subclass works with `SpatialIndex` without changes; custom procedural generator injection
  - _Requirements: 15.1, 15.2, 15.3, 15.4_

- [ ] 16. Final checkpoint — all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests use `hypothesis` with `@settings(max_examples=100)` and are tagged `# Feature: dec-pomdp-environment, Property N: <text>`
- Checkpoints ensure incremental validation before proceeding to the next phase
