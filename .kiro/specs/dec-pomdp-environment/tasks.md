# Implementation Plan: Continuous Physics-Based Dec-POMDP Environment

## Overview

Incremental implementation of the continuous 2D physics-based asymmetric Dec-POMDP environment in Python. Each task builds on the previous, ending with a fully wired environment ready for integration with external learning algorithms. The design document and requirements are the authoritative references throughout.

`latency_buffer.py` is already implemented and tested — it is not a task here. Property tests for the latency buffer (Properties 13 and 14) are included as sub-tasks under the communication wiring task where the buffer is integrated.

## Tasks

- [ ] 1. Project structure, errors, and configuration loader
  - Create directory layout: `env/`, `env/tests/`, `env/tests/properties/`
  - Create `env/__init__.py`
  - Implement `env/errors.py` with the full exception hierarchy: `DecPOMDPError`, `ConfigValidationError`, `MessageDimensionError`, `EpisodeTerminatedError`, `GenerationFailedError`, `InvalidObstacleError` (subclass of `ConfigValidationError`)
  - Implement `env/config_loader.py`: `EnvConfig` dataclass (all fields per design) and `ConfigLoader.load(path)` that validates all required fields and raises `ConfigValidationError` naming the offending field; validate obstacle shape defs and raise `InvalidObstacleError` for invalid geometry
  - Create a sample `Config/config.json` matching the JSON schema in the design
  - Write `env/tests/test_config_loader.py`: unit tests for all required fields present, each required field missing, optional fields defaulting correctly, all three obstacle shape types parsed, invalid obstacle raises `InvalidObstacleError`
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.7, 6.5_

  - [ ]* 1.1 Write property test for config error naming (Property 1)
    - **Property 1: Config Error Names the Offending Field**
    - **Validates: Requirements 1.5**
    - Use `st.sampled_from(REQUIRED_FIELDS)` to generate missing/invalid fields; assert `ConfigValidationError` message contains the exact field name

- [ ] 2. Entity hierarchy
  - Implement `env/entity.py`: abstract `Entity` dataclass with `id: str`, `x: float`, `y: float`, `static: bool`, `collidable: bool`
  - Implement `env/objects.py`: concrete dataclasses `AgentA`, `AgentB` (adds `heading`, `speed`, `vx`, `vy`), `Obstacle` (adds `shape_def: RectDef | CircleDef | PolygonDef`), `Target`; set correct `static`/`collidable` defaults per design hierarchy table
  - Implement shape definition dataclasses in `env/objects.py`: `RectDef`, `CircleDef`, `PolygonDef`
  - Write `env/tests/test_entity.py`: `isinstance` checks, flag defaults for each concrete type, `AgentB` field defaults, `Obstacle` shape_def field
  - _Requirements: 2.2, 2.3, 3.1, 3.2, 3.4, 3.5, 6.1_

- [ ] 3. Physics engine (pymunk wrapper)
  - Implement `env/physics_engine.py`: `PhysicsEngine` class wrapping a `pymunk.Space`
  - `__init__`: create space, add four static segment shapes for world boundary walls
  - `add_agent_b(x, y, agent_radius)`: create dynamic circular body for Agent B
  - `add_obstacle(shape_def)`: create static shape for `RectDef`, `CircleDef`, or `PolygonDef` and add to space
  - `set_velocity(vx, vy)`: set Agent B's body velocity
  - `step(dt=1.0)`: advance pymunk space, resolving all collisions
  - `get_agent_b_position() -> tuple[float, float]`: query position after integration
  - `get_agent_b_velocity() -> tuple[float, float]`: query actual velocity after collision response
  - `reset()`: remove all bodies and shapes, recreate boundary segments
  - Write `env/tests/test_physics_engine.py`: unit tests for all three obstacle shape types registering without error, boundary walls created, Agent B body created, velocity set and queried, `reset()` clears state
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 6.2_

  - [ ]* 3.1 Write property test for physics engine prevents penetration (Property 6)
    - **Property 6: Physics Engine Prevents Penetration**
    - **Validates: Requirements 4.5, 5.5**
    - Generate random obstacle layouts and action sequences; assert Agent B's circular body never overlaps an obstacle or boundary by more than 0.01 world units

  - [ ]* 3.2 Write property test for boundary containment (Property 7)
    - **Property 7: Boundary Containment**
    - **Validates: Requirements 2.6, 4.4**
    - For any sequence of steps, assert `agent_radius ≤ x ≤ world_width − agent_radius` and `agent_radius ≤ y ≤ world_height − agent_radius`

- [ ] 4. Checkpoint — physics foundation complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Procedural generator
  - Implement `env/procedural_gen.py`: `ProceduralGenerator(config)` with `generate(seed) -> GeneratedLayout` using `random.Random(seed)` (not global state)
  - Place `AgentA`, `AgentB`, `Target`, and `Obstacle` entities at valid float positions within world bounds
  - Enforce: all positions within `[0, world_width] × [0, world_height]`, no obstacle overlaps spawn positions, `dist(AgentB, Target) > capture_radius`, `dist(AgentB, Target) >= min_separation` when configured
  - Retry on constraint violation up to a budget; raise `GenerationFailedError` (with seed and config details) if budget exhausted
  - Register all generated obstacle shapes with the `PhysicsEngine` before the first step
  - Write `env/tests/test_procedural_gen.py`: unit tests for seed reproducibility, bounds enforcement, separation constraint, `GenerationFailedError` on impossible config
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

  - [ ]* 5.1 Write property test for reproducibility (Property 2)
    - **Property 2: Reproducibility — Same Seed Produces Identical Layout**
    - **Validates: Requirements 1.6, 7.3, 7.4, 13.4**
    - Use `st.integers()` for seeds; call `generate(seed)` twice, assert all entity positions are identical

  - [ ]* 5.2 Write property test for all entities within world bounds after reset (Property 3)
    - **Property 3: All Entities Within World Bounds After Reset**
    - **Validates: Requirements 2.1, 7.1**
    - For any seed, assert every entity satisfies `0.0 ≤ x ≤ world_width` and `0.0 ≤ y ≤ world_height`

  - [ ]* 5.3 Write property test for initialization separation invariant (Property 8)
    - **Property 8: Initialization Separation Invariant**
    - **Validates: Requirements 7.5**
    - For any seed, assert `dist(AgentB, Target) > capture_radius` after `generate(seed)`

  - [ ]* 5.4 Write property test for minimum separation enforced (Property 9)
    - **Property 9: Minimum Separation Enforced**
    - **Validates: Requirements 7.6**
    - Use configs with `min_separation > 0`; assert Euclidean distance between AgentB and Target ≥ `min_separation`

- [ ] 6. Checkpoint — generation and placement complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Velocity-based movement system
  - Implement the heading/speed update logic in `env/environment.py` (or a dedicated helper): clamp `Δheading` to `±max_angular_velocity`, clamp resulting speed to `[0, max_speed]`, compute `vx = speed * cos(heading)`, `vy = speed * sin(heading)`
  - Write `env/tests/test_movement.py`: unit tests for clamping at limits, zero-speed action, max-speed action, heading wrap-around
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.6_

  - [ ]* 7.1 Write property test for velocity magnitude never exceeds max_speed (Property 4)
    - **Property 4: Agent_B Velocity Magnitude Never Exceeds max_speed**
    - **Validates: Requirements 5.2**
    - Use `st.lists(st.tuples(st.floats(allow_nan=False), st.floats(allow_nan=False)))` for action sequences; assert `sqrt(vx² + vy²) ≤ max_speed` after every step

  - [ ]* 7.2 Write property test for heading change clamped to max_angular_velocity (Property 5)
    - **Property 5: Heading Change Clamped to max_angular_velocity**
    - **Validates: Requirements 5.2**
    - Use `st.floats(allow_nan=False)` for arbitrary `Δheading`; assert `|heading_new − heading_old| ≤ max_angular_velocity`

- [ ] 8. Observation interface
  - Implement `generate_observations()` in `env/environment.py` returning `ObsA` (TypedDict with `agent_a`, `agent_b`, `agent_b_velocity`, `target`, `obstacles`, `timestep`) and `ObsB = {}`
  - Obstacle geometry in `obs_a["obstacles"]` uses the schema from the design (type + shape params)
  - Write `env/tests/test_environment.py`: unit tests for `reset()` returning `(obs_a, obs_b)` tuple, `obs_a` key set consistent across steps, `obs_b` always `{}`, timestep field present
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [ ]* 8.1 Write property test for Agent A observation completeness and consistency (Property 10)
    - **Property 10: Agent_A Observation Completeness and Consistency**
    - **Validates: Requirements 8.1, 8.4**
    - For any seed and step sequence, assert `obs_a` contains all entity positions and obstacle geometry, and the key set is identical at every timestep within an episode

  - [ ]* 8.2 Write property test for Agent B observation always empty (Property 11)
    - **Property 11: Agent_B Observation Is Always Empty**
    - **Validates: Requirements 8.2**
    - For any environment state and any sequence of steps, assert `obs_b == {}`

- [ ] 9. Communication interface and latency buffer wiring
  - Implement message validation at the start of `step()`: raise `MessageDimensionError` (stating actual length) if `len(message_a) != 16`
  - Wire `latency_buffer.push(message_a)` and `delayed_msg = latency_buffer.pop()` into the step pipeline; return `delayed_msg` in `info["message"]`
  - Write unit tests in `env/tests/test_environment.py`: valid 16-float message accepted, wrong-length message raises `MessageDimensionError` before any state mutation
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 10.1, 10.2, 10.3, 10.4_

  - [ ]* 9.1 Write property test for message dimension validation (Property 12)
    - **Property 12: Message Dimension Validation**
    - **Validates: Requirements 9.1, 9.2**
    - Use `st.lists(st.floats(allow_nan=False), min_size=0, max_size=32)` for varying lengths; assert length-16 accepted, all others raise `MessageDimensionError`

  - [ ]* 9.2 Write property test for latency buffer round-trip (Property 13)
    - **Property 13: Latency Buffer Round-Trip**
    - **Validates: Requirements 10.2, 10.4, 10.5**
    - Use `st.lists(st.floats(allow_nan=False), min_size=16, max_size=16)` and `st.integers(0, 10)` for tau; push message, pop τ times discarding, assert final pop equals original message

  - [ ]* 9.3 Write property test for zero vector before buffer fills (Property 14)
    - **Property 14: Zero Vector Before Buffer Fills**
    - **Validates: Requirements 10.3**
    - Use `st.integers(1, 20)` for tau; assert first τ pops on a fresh `LatencyBuffer` all return `[0.0] * 16`

- [ ] 10. Reward, termination, and step pipeline
  - Implement `compute_reward_and_termination()` in `env/environment.py`: Euclidean distance check against `capture_radius` (+1/True), timeout check (0/True), ongoing (0/False)
  - Implement `EpisodeTerminatedError` guard at `step()` entry (before any state mutation)
  - Wire the complete ordered step pipeline per the design spec (steps 1–12)
  - Implement `state_dict()` returning full current state: Agent B position and velocity, Target position, Obstacle geometries, timestep, last reward
  - Write `env/tests/test_reward.py`: unit tests for capture, timeout, ongoing, step-on-terminated
  - Write unit tests in `env/tests/test_environment.py`: pipeline ordering (mock-based verifying call sequence), `state_dict()` keys match documented schema
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 12.1, 12.2, 12.3, 15.2_

  - [ ]* 10.1 Write property test for capture triggers positive reward and termination (Property 15)
    - **Property 15: Capture Triggers Positive Reward and Termination**
    - **Validates: Requirements 11.1, 11.2**
    - Place Agent B within `capture_radius` of Target; assert `reward > 0` and `terminated == True`

  - [ ]* 10.2 Write property test for no-capture steps return zero reward (Property 16)
    - **Property 16: No-Capture Steps Return Zero Reward**
    - **Validates: Requirements 11.4**
    - Generate step sequences where Agent B never reaches Target and episode has not timed out; assert every step returns `reward == 0` and `terminated == False`

  - [ ]* 10.3 Write property test for timeout terminates with zero reward (Property 17)
    - **Property 17: Timeout Terminates with Zero Reward**
    - **Validates: Requirements 11.3**
    - Use configs with small `max_steps`; run exactly `max_steps` steps without capture; assert `terminated == True` and `reward == 0`

  - [ ]* 10.4 Write property test for step on terminated episode raises error (Property 18)
    - **Property 18: Step on Terminated Episode Raises Error**
    - **Validates: Requirements 11.5, 12.2**
    - After termination (capture or timeout), assert `step()` raises `EpisodeTerminatedError`

  - [ ]* 10.5 Write property test for timestep increments by one per step (Property 19)
    - **Property 19: Timestep Increments by One Per Step**
    - **Validates: Requirements 12.3**
    - Use `st.integers(1, 100)` for step counts; assert `env.timestep == n` after n steps

  - [ ]* 10.6 Write property test for state dict accuracy (Property 21)
    - **Property 21: State Dict Reflects Current Entity Positions and Velocity**
    - **Validates: Requirements 15.2**
    - For any environment state, assert `state_dict()` Agent B position and velocity match direct entity attribute queries

- [ ] 11. Checkpoint — full environment wired
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Reset mechanism
  - Implement `reset(seed=None)` in `env/environment.py`: clear all entities, reset timestep to 0, clear latency buffer, call `physics_engine.reset()`, invoke procedural generator, register all shapes with physics engine, return `(obs_a, obs_b)`
  - Support optional seed override (uses config seed if not provided)
  - Write unit tests: reset returns correct `(obs_a, obs_b)` tuple, `timestep == 0`, buffer cleared (first pop returns zero vector), new seed produces different layout
  - _Requirements: 13.1, 13.2, 13.3, 13.4_

  - [ ]* 12.1 Write property test for reset clears state (Property 20)
    - **Property 20: Reset Clears State**
    - **Validates: Requirements 13.1**
    - After mid-episode or terminated state, call `reset()`; assert `timestep == 0` and first τ pops of the buffer return zero vectors

- [ ] 13. Pygame renderer
  - Implement `env/renderer.py`: `Renderer(config)` opening a Pygame window sized to `world_width × world_height`
  - `draw(state: dict) -> bool`: render Agent B as filled circle, Agent A as distinct marker, Target as distinct marker, each Obstacle as filled shape matching geometry; display timestep and reward in window title; return `False` if window closed
  - `close()`: destroy window and quit Pygame
  - Import `renderer.py` inside `environment.py` only when `config.render is True` (zero import cost when disabled)
  - Write `env/tests/test_renderer.py`: unit test that Pygame is not imported when `render=False`; renderer tests marked to skip in CI if no display
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

- [ ] 14. Logging, state_dict, and extensibility
  - Implement configurable logging in `env/environment.py` using Python's `logging` module at levels controlled by `log_level` config field; log entity positions, velocity updates, collision events, reward signals
  - Verify no hardcoded world dimensions exist anywhere in environment logic (all from `EnvConfig`)
  - Add support for injecting an alternative `ProceduralGenerator` subclass via `DecPOMDPEnvironment.__init__` parameter
  - Write unit tests: custom entity subclass works without changes to `PhysicsEngine`; custom procedural generator injection; environment fully functional with `log_level="WARNING"`
  - _Requirements: 15.1, 15.3, 16.1, 16.2, 16.3, 16.4_

- [ ] 15. Final checkpoint — all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- `latency_buffer.py` is already implemented and tested — do not reimplement it
- Each task references specific requirements for traceability
- Property tests use `hypothesis` with `@settings(max_examples=100)` and are tagged `# Feature: dec-pomdp-environment, Property N: <property_text>`
- Checkpoints ensure incremental validation before proceeding to the next phase
