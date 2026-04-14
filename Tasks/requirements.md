# Requirements Document

## Introduction

This document specifies the requirements for the continuous physics-based environment of an asymmetric Decentralized Partially Observable Markov Decision Process (Dec-POMDP) research system. The environment hosts two agents with strictly asymmetric roles: Agent A (Observer) has full state visibility and acts as a pure communicator, while Agent B (Actor) is completely blind and relies solely on delayed messages from Agent A to navigate toward a target. The environment implements continuous 2D physics using pymunk (Chipmunk-based), renders live visualisation via Pygame, and exposes clean interfaces for integration with external learning algorithms.

The Dec-POMDP formal structure is unchanged: ⟨𝒮, 𝒜, 𝒵, 𝒯, 𝒪, ℛ, γ⟩. Only the environment physics change — from a discrete 64×64 grid to a continuous 2D world with velocity-based movement, geometric obstacles, and capture-radius termination.

---

## Glossary

- **Environment**: The simulation system managing the continuous 2D world, all entities, the physics engine, the step pipeline, and episode lifecycle.
- **World**: The continuous 2D coordinate space in which all entities exist, bounded by a configurable rectangle of dimensions `world_width × world_height` (floating-point units).
- **Agent_A**: The Observer agent. Stationary. Receives the full environment state as its observation (positions, velocities, obstacle geometry) and sends a continuous message vector each timestep. Has no movement action.
- **Agent_B**: The Actor agent. Receives no environment state observation. Moves continuously each timestep via velocity-based steering actions, guided solely by messages received from Agent_A.
- **Target**: The static entity that Agent_B must approach within `capture_radius` to complete an episode.
- **Obstacle**: A static, collidable geometric shape (rectangular wall, circular pillar, or convex polygon) that blocks Agent_B movement via continuous collision detection.
- **Entity**: The base abstraction for any object existing in the World, including agents, obstacles, and the target.
- **Physics_Engine**: The pymunk simulation instance responsible for continuous collision detection, collision response, and body integration.
- **Message**: A continuous vector m_t ∈ ℝ¹⁶ transmitted by Agent_A to Agent_B each timestep.
- **Latency_Buffer**: The FIFO queue that holds outgoing messages from Agent_A and releases them to Agent_B after a fixed delay τ timesteps.
- **τ (tau)**: The integer communication latency parameter specifying how many timesteps a message is delayed before delivery to Agent_B.
- **Episode**: A single run of the simulation from reset to termination.
- **Config**: The JSON configuration file that parameterizes the Environment at initialization.
- **Observation**: The structured data returned to an agent at each timestep representing its view of the world.
- **Capture**: The event in which Agent_B's position is within `capture_radius` of the Target's position, triggering episode success.
- **Step**: One full execution of the Environment's update pipeline, advancing the simulation by one timestep.
- **Velocity**: A 2D vector (vx, vy) representing Agent_B's current speed and direction of travel.
- **Heading**: The angle (in radians) of Agent_B's current direction of travel, measured from the positive x-axis.
- **capture_radius**: The maximum Euclidean distance between Agent_B and the Target at which Capture is declared.
- **agent_radius**: The radius of Agent_B's circular collision body used by the Physics_Engine.
- **max_speed**: The maximum magnitude of Agent_B's velocity vector.
- **max_angular_velocity**: The maximum rate of change of Agent_B's heading per timestep (radians/step).
- **Renderer**: The optional Pygame window that visualises the live environment state during development and evaluation.

---

## Requirements

### Requirement 1: Configuration System

**User Story:** As a researcher, I want all environment parameters defined in a single JSON config file, so that I can reproduce and modify experiments without changing source code.

#### Acceptance Criteria

1. THE Config SHALL define the following required parameters: `world_width`, `world_height`, `random_seed`, `max_steps`, and `tau`.
2. THE Config SHALL define the following physics parameters: `agent_radius`, `max_speed`, `max_angular_velocity`, and `capture_radius`.
3. THE Config SHALL define obstacle configuration as either a list of explicit obstacle definitions or a procedural generation parameter block.
4. WHEN the Environment is initialized, THE Config_Loader SHALL read and validate all parameters from the Config file before any entity is created.
5. IF the Config file is missing or malformed, THEN THE Config_Loader SHALL raise a descriptive error identifying the missing or invalid field by name.
6. WHEN the same Config and seed are provided across multiple runs, THE Environment SHALL produce identical initial states (reproducibility).
7. THE Config SHALL use JSON format.

---

### Requirement 2: World and Coordinate Representation

**User Story:** As a developer, I want the world represented as a continuous 2D floating-point coordinate system, so that entity positions and velocities can be represented with sub-unit precision.

#### Acceptance Criteria

1. THE World SHALL be a continuous 2D coordinate space where valid positions are floating-point pairs (x, y) with 0.0 ≤ x ≤ world_width and 0.0 ≤ y ≤ world_height.
2. THE Environment SHALL store all entity positions as floating-point (x, y) coordinate pairs.
3. THE Environment SHALL store Agent_B's velocity as a floating-point vector (vx, vy).
4. WHEN an entity position is queried, THE Environment SHALL return the entity's current floating-point (x, y) coordinate pair.
5. WHEN Agent_B's velocity is queried, THE Environment SHALL return the current (vx, vy) vector.
6. THE World SHALL be bounded by solid boundary walls that prevent Agent_B from leaving the world extents.

---

### Requirement 3: Entity Abstraction Layer

**User Story:** As a developer, I want a base entity abstraction, so that all world objects share a consistent interface and can be extended without modifying core logic.

#### Acceptance Criteria

1. THE Entity SHALL have a unique identifier, a floating-point (x, y) position, and boolean properties: `static`, `collidable`.
2. THE Environment SHALL support the following concrete entity types derived from Entity: Agent_A, Agent_B, Obstacle, Target.
3. WHEN a new entity type is added, THE Environment SHALL require no changes to the Physics_Engine integration or collision logic, provided the new type sets its `collidable` property correctly.
4. THE Target SHALL be static and non-collidable by the Physics_Engine (Agent_B may pass through its position; Capture is detected by distance, not collision).
5. THE Obstacle SHALL be static and collidable (Agent_B is physically blocked by Obstacle geometry via the Physics_Engine).

---

### Requirement 4: Physics Engine and Collision Detection

**User Story:** As a developer, I want continuous collision detection via pymunk, so that Agent_B interacts correctly with geometric obstacles and world boundaries.

#### Acceptance Criteria

1. THE Physics_Engine SHALL use pymunk as the underlying 2D physics library.
2. THE Physics_Engine SHALL represent Agent_B as a dynamic circular body with radius `agent_radius`.
3. THE Physics_Engine SHALL represent each Obstacle as a static shape: a rectangular box, a circular pillar, or a convex polygon, as specified in Config.
4. THE Physics_Engine SHALL represent world boundaries as four static segment shapes enclosing the World extents.
5. WHEN Agent_B's movement would intersect an Obstacle or boundary, THE Physics_Engine SHALL resolve the collision and prevent Agent_B from passing through the shape.
6. THE Physics_Engine SHALL advance the simulation by a fixed timestep each Step, integrating Agent_B's velocity and resolving all collisions before returning the new state.
7. THE Environment SHALL query Agent_B's position from the Physics_Engine after each integration step.

---

### Requirement 5: Velocity-Based Movement System

**User Story:** As a researcher, I want Agent_B to move via velocity-based steering actions, so that movement is smooth and continuous like an agent navigating a physical space.

#### Acceptance Criteria

1. THE Environment SHALL define Agent_B's action as a pair (Δheading, Δspeed) where Δheading is a heading change in radians and Δspeed is a speed increment in world units per step.
2. WHEN Agent_B selects an action, THE Environment SHALL clamp the resulting heading change to ±max_angular_velocity and the resulting speed to [0, max_speed].
3. WHEN Agent_B's heading and speed are updated, THE Environment SHALL compute the new velocity vector as (speed × cos(heading), speed × sin(heading)).
4. THE Environment SHALL apply the updated velocity to Agent_B's physics body before the Physics_Engine integration step.
5. WHILE Agent_B is in contact with an Obstacle or boundary, THE Physics_Engine SHALL prevent penetration and may reduce Agent_B's velocity component normal to the surface.
6. THE Environment SHALL apply movement updates after processing communication for the current timestep.

---

### Requirement 6: Geometric Obstacle Representation

**User Story:** As a researcher, I want obstacles defined as geometric shapes, so that the environment supports rich spatial structure beyond simple cell blocking.

#### Acceptance Criteria

1. THE Environment SHALL support three obstacle shape types: rectangular walls (defined by centre, width, height, and rotation angle), circular pillars (defined by centre and radius), and convex polygons (defined by an ordered list of vertices).
2. WHEN the Environment is initialized, THE Environment SHALL register each Obstacle's shape with the Physics_Engine as a static body.
3. THE Environment SHALL expose each Obstacle's geometry (shape type and parameters) as part of Agent_A's observation.
4. WHEN Agent_B's circular body contacts an Obstacle shape, THE Physics_Engine SHALL resolve the collision so that Agent_B does not penetrate the Obstacle.
5. IF an obstacle definition in Config specifies an invalid shape (e.g. non-convex polygon, zero-area rectangle), THEN THE Config_Loader SHALL raise a descriptive error identifying the invalid obstacle.

---

### Requirement 7: Procedural Generation

**User Story:** As a researcher, I want each episode to start with a procedurally generated layout, so that agents must generalize rather than memorize fixed configurations.

#### Acceptance Criteria

1. WHEN the Environment is reset, THE Procedural_Generator SHALL place Agent_A, Agent_B, and the Target at valid floating-point positions within the World bounds.
2. WHEN the Environment is reset with procedural obstacles enabled, THE Procedural_Generator SHALL generate obstacle shapes at valid positions that do not overlap Agent_A, Agent_B, or the Target spawn positions.
3. THE Procedural_Generator SHALL use the random seed from Config to initialize its random number generator, ensuring reproducibility.
4. WHEN a fixed seed is provided, THE Environment SHALL produce the same entity layout on every reset call with that seed.
5. THE Procedural_Generator SHALL ensure Agent_B and the Target are not placed within `capture_radius` of each other at spawn.
6. WHERE a minimum separation distance is specified in Config, THE Procedural_Generator SHALL enforce that the Euclidean distance between Agent_B's initial position and the Target is at least that value.
7. THE Procedural_Generator SHALL register all generated Obstacle shapes with the Physics_Engine before the first Step of the episode.

---

### Requirement 8: Observation Interface

**User Story:** As a researcher, I want well-defined observation outputs for each agent, so that learning algorithms can consume them without environment-specific parsing.

#### Acceptance Criteria

1. WHEN observations are generated, THE Environment SHALL return Agent_A's observation as the full environment state, including: Agent_A position, Agent_B position and velocity, Target position, and the geometry of all Obstacles.
2. WHEN observations are generated, THE Environment SHALL return Agent_B's observation as an empty structure (z_B = ∅), containing no environment state information.
3. THE Environment SHALL generate observations at every timestep as part of the Step pipeline.
4. THE Environment SHALL return observations in a consistent, documented format that does not change between timesteps within an episode.
5. WHEN the Environment is reset, THE Environment SHALL return initial observations for both agents before any Step is taken.
6. THE Environment SHALL include the current timestep index in Agent_A's observation.

---

### Requirement 9: Communication Interface

**User Story:** As a researcher, I want the environment to manage message passing between agents, so that the communication channel is decoupled from the learning algorithm implementations.

#### Acceptance Criteria

1. WHEN Agent_A provides a message m_t, THE Environment SHALL accept a vector of exactly 16 floating-point values.
2. IF Agent_A provides a message vector of length other than 16, THEN THE Environment SHALL raise a descriptive error stating the actual length received.
3. THE Environment SHALL pass the received message to the Latency_Buffer each timestep before delivering any message to Agent_B.
4. THE Environment SHALL deliver to Agent_B only the message released by the Latency_Buffer, not the message submitted in the current timestep.
5. THE Environment SHALL not modify the content of any message during transmission.

---

### Requirement 10: Latency Buffer

**User Story:** As a researcher, I want artificial network latency τ applied to messages, so that I can study how communication delay affects emergent coordination.

#### Acceptance Criteria

1. THE Latency_Buffer SHALL store messages in a FIFO queue with capacity τ + 1.
2. WHEN a message is submitted at timestep t, THE Latency_Buffer SHALL release that message to Agent_B at timestep t + τ.
3. WHEN timestep t < τ (early episode steps before any message has aged τ steps), THE Latency_Buffer SHALL deliver a zero vector of length 16 to Agent_B.
4. WHEN τ = 0, THE Latency_Buffer SHALL deliver the current timestep's message to Agent_B without delay.
5. FOR ALL valid message sequences, submitting a message and retrieving it after τ steps SHALL return the original unmodified message (round-trip property).

---

### Requirement 11: Capture and Termination

**User Story:** As a researcher, I want a clear capture condition and termination logic, so that the joint reward is unambiguous and episodes end deterministically.

#### Acceptance Criteria

1. WHEN the Euclidean distance between Agent_B's position and the Target's position is less than or equal to `capture_radius`, THE Environment SHALL declare Capture and assign a positive reward to the joint reward signal.
2. WHEN Capture occurs, THE Environment SHALL set the episode status to terminated.
3. WHEN the current timestep reaches `max_steps`, THE Environment SHALL set the episode status to terminated with a reward of 0.
4. WHILE the episode is active and Capture has not occurred, THE Environment SHALL assign a reward of 0 each timestep.
5. WHEN the episode is terminated, THE Environment SHALL not process further Steps until reset.

---

### Requirement 12: Step Pipeline

**User Story:** As a developer, I want a well-defined step pipeline, so that the simulation update order is deterministic and reproducible.

#### Acceptance Criteria

1. THE Environment SHALL execute each Step in the following fixed order: (1) validate episode is active, (2) accept Agent_B's action and Agent_A's message, (3) submit message to Latency_Buffer, (4) retrieve delayed message from Latency_Buffer, (5) apply Agent_B's steering action to update heading and speed, (6) advance the Physics_Engine by one timestep, (7) query Agent_B's new position and velocity from the Physics_Engine, (8) compute reward and check termination, (9) generate and return observations.
2. WHEN a Step is called on a terminated episode, THE Environment SHALL raise an error indicating the episode must be reset before stepping.
3. THE Environment SHALL increment the timestep counter by exactly 1 on each Step.

---

### Requirement 13: Reset Mechanism

**User Story:** As a developer, I want a reset method that fully reinitializes the environment, so that each episode starts from a clean, valid state.

#### Acceptance Criteria

1. WHEN reset is called, THE Environment SHALL clear all entities, reset the timestep counter to 0, clear the Latency_Buffer, and reset the Physics_Engine to an empty state.
2. WHEN reset is called, THE Environment SHALL invoke the Procedural_Generator to place all entities at new valid positions and register all shapes with the Physics_Engine.
3. WHEN reset is called, THE Environment SHALL return initial observations for both agents.
4. WHEN reset is called with a new seed, THE Environment SHALL use that seed for the subsequent episode's procedural generation.

---

### Requirement 14: Pygame Renderer

**User Story:** As a developer, I want a live Pygame visualisation window, so that I can observe agent behaviour and debug the environment during development and evaluation.

#### Acceptance Criteria

1. WHERE the renderer is enabled in Config, THE Renderer SHALL open a Pygame window sized to `world_width × world_height` pixels (or a scaled equivalent).
2. WHEN each Step completes, THE Renderer SHALL draw the current environment state: Agent_B as a filled circle, Agent_A as a distinct marker, the Target as a distinct marker, and each Obstacle as a filled shape matching its geometry.
3. THE Renderer SHALL use distinct colours for Agent_A, Agent_B, the Target, and Obstacles.
4. WHEN the Pygame window is closed by the user, THE Renderer SHALL signal the Environment to stop the current episode.
5. WHERE the renderer is disabled, THE Environment SHALL run without importing or initializing Pygame, incurring no rendering overhead.
6. THE Renderer SHALL display the current timestep and episode reward in the window title or as an overlay.

---

### Requirement 15: Debugging and Logging

**User Story:** As a developer, I want structured logging, so that I can inspect environment state and diagnose issues without relying solely on the visual renderer.

#### Acceptance Criteria

1. THE Environment SHALL log entity positions, velocity updates, collision events, and reward signals at a configurable verbosity level controlled by the `log_level` Config parameter.
2. THE Environment SHALL expose a `state_dict()` method that returns the full current state as a structured dictionary, including Agent_B's position and velocity, Target position, Obstacle geometries, timestep, and last reward.
3. THE Environment SHALL remain fully functional with logging disabled (log_level = "WARNING" or higher).

---

### Requirement 16: Extensibility

**User Story:** As a researcher, I want the environment to be extensible, so that new entity types, world sizes, and generation strategies can be added without restructuring core modules.

#### Acceptance Criteria

1. THE Environment SHALL read world dimensions exclusively from Config, with no hardcoded size values in environment logic.
2. WHEN a new Entity subclass is introduced, THE Environment SHALL require no changes to the Step pipeline or Physics_Engine integration, provided the subclass registers its shapes correctly.
3. THE Environment SHALL remain fully independent of any learning algorithm, neural network, or optimizer code.
4. WHERE an alternative procedural generation strategy is provided, THE Environment SHALL accept it as a configurable parameter without modifying core environment logic.

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system.*

---

### Property 1: Config Error Names the Offending Field

For any required config field, if that field is absent or has an invalid type in the JSON config, the `ConfigValidationError` raised SHALL contain the name of that field in its message.

**Validates: Requirement 1.5**

---

### Property 2: Reproducibility — Same Seed Produces Identical Layout

For any valid config and any integer seed, calling `reset(seed)` twice SHALL produce identical entity positions for all entities (Agent_A, Agent_B, Target, all Obstacles).

**Validates: Requirements 1.6, 7.3, 7.4, 13.4**

---

### Property 3: All Entities Within World Bounds After Reset

For any valid config and any seed, after `reset()`, every entity's (x, y) position SHALL satisfy `0.0 ≤ x ≤ world_width` and `0.0 ≤ y ≤ world_height`.

**Validates: Requirements 2.1, 7.1**

---

### Property 4: Agent_B Velocity Magnitude Never Exceeds max_speed

For any sequence of actions applied to Agent_B, the magnitude of Agent_B's velocity vector `sqrt(vx² + vy²)` SHALL never exceed `max_speed`.

**Validates: Requirements 5.2**

---

### Property 5: Heading Change Clamped to max_angular_velocity

For any action with Δheading of arbitrary magnitude, the absolute change in Agent_B's heading per step SHALL not exceed `max_angular_velocity`.

**Validates: Requirements 5.2**

---

### Property 6: Physics Engine Prevents Penetration

For any sequence of steps, Agent_B's circular body SHALL never overlap an Obstacle shape or world boundary by more than a negligible numerical tolerance (≤ 0.01 world units).

**Validates: Requirements 4.5, 5.5**

---

### Property 7: Boundary Containment

For any sequence of steps, Agent_B's position SHALL satisfy `agent_radius ≤ x ≤ world_width − agent_radius` and `agent_radius ≤ y ≤ world_height − agent_radius`.

**Validates: Requirements 2.6, 4.4**

---

### Property 8: Initialization Separation Invariant

For any valid config and any seed, after `reset()`, the Euclidean distance between Agent_B's initial position and the Target's position SHALL be greater than `capture_radius`.

**Validates: Requirements 7.5**

---

### Property 9: Minimum Separation Enforced

For any valid config with `min_separation > 0` and any seed, after `reset()`, the Euclidean distance between Agent_B and the Target SHALL be ≥ `min_separation`.

**Validates: Requirements 7.6**

---

### Property 10: Agent_A Observation Completeness and Consistency

For any environment state and any sequence of steps, Agent_A's observation SHALL contain the positions of all entities and the geometry of all Obstacles, and the set of keys in `obs_a` SHALL be identical at every timestep within an episode.

**Validates: Requirements 8.1, 8.4**

---

### Property 11: Agent_B Observation Is Always Empty

For any environment state, Agent_B's observation SHALL be an empty structure containing no environment state information.

**Validates: Requirements 8.2**

---

### Property 12: Message Dimension Validation

For any list of floats of length exactly 16, `step()` SHALL accept it without raising a dimension error. For any list of length ≠ 16, `step()` SHALL raise `MessageDimensionError`.

**Validates: Requirements 9.1, 9.2**

---

### Property 13: Latency Buffer Round-Trip

For any message `m` (a list of 16 floats) and any τ ≥ 0, pushing `m` into a fresh `LatencyBuffer(tau=τ)` and then calling `pop()` exactly τ times (discarding results) followed by one final `pop()` SHALL return a value equal to `m` with no modification.

**Validates: Requirements 10.2, 10.4, 10.5**

---

### Property 14: Zero Vector Before Buffer Fills

For any τ > 0, the first τ calls to `pop()` on a freshly initialized `LatencyBuffer` (before any `push`) SHALL return `[0.0] * 16`.

**Validates: Requirements 10.3**

---

### Property 15: Capture Triggers Positive Reward and Termination

For any valid environment state where Agent_B is moved to within `capture_radius` of the Target, the step SHALL return `reward > 0` and `terminated == True`.

**Validates: Requirements 11.1, 11.2**

---

### Property 16: No-Capture Steps Return Zero Reward

For any sequence of steps in which Agent_B does not come within `capture_radius` of the Target and the episode has not timed out, every step SHALL return `reward == 0` and `terminated == False`.

**Validates: Requirements 11.4**

---

### Property 17: Timeout Terminates with Zero Reward

For any config with `max_steps = N`, after exactly N steps without capture, the environment SHALL return `terminated == True` and `reward == 0`.

**Validates: Requirements 11.3**

---

### Property 18: Step on Terminated Episode Raises Error

For any terminated episode (by capture or timeout), calling `step()` SHALL raise `EpisodeTerminatedError`.

**Validates: Requirements 11.5, 12.2**

---

### Property 19: Timestep Increments by One Per Step

For any sequence of n valid steps, `env.timestep` SHALL equal n after those steps.

**Validates: Requirements 12.3**

---

### Property 20: Reset Clears State

For any environment state (mid-episode or terminated), after `reset()`, the timestep counter SHALL be 0 and the Latency_Buffer SHALL be empty (all pops return zero vectors).

**Validates: Requirements 13.1**

---

### Property 21: State Dict Reflects Current Entity Positions and Velocity

For any environment state, `state_dict()` SHALL contain Agent_B's position and velocity, and those values SHALL match the values returned by direct entity queries.

**Validates: Requirements 15.2**
