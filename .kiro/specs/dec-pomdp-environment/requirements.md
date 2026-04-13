# Requirements Document

## Introduction

This document specifies the requirements for the grid environment of an asymmetric Decentralized Partially Observable Markov Decision Process (Dec-POMDP) research system. The environment hosts two agents with strictly asymmetric roles: Agent A (Observer) has full state visibility and acts as a pure communicator, while Agent B (Actor) is completely blind and relies solely on delayed messages from Agent A to navigate toward a target. The environment must faithfully implement the formal Dec-POMDP tuple, support procedural episode generation, enforce a latency-buffered communication channel, and expose clean interfaces for integration with external learning algorithms.

---

## Glossary

- **Environment**: The simulation system managing the 64×64 discrete grid, all entities, the step pipeline, and episode lifecycle.
- **Grid**: The 64×64 discrete coordinate space in which all entities exist, indexed by integer (x, y) pairs where 0 ≤ x < 64 and 0 ≤ y < 64.
- **Agent_A**: The Observer agent. Receives the full environment state as its observation and sends a continuous message vector each timestep. Has no movement action.
- **Agent_B**: The Actor agent. Receives no environment state observation. Moves 8-directionally each timestep based solely on messages received from Agent_A.
- **Target**: The static entity that Agent_B must reach to complete an episode.
- **Obstacle**: A static, collidable entity that blocks Agent_B movement, procedurally placed each episode.
- **Entity**: The base abstraction for any object occupying a position in the Grid, including agents, obstacles, and the target.
- **Spatial_Index**: The data structure that maps Grid positions to the entities occupying them, used for collision detection and movement validation.
- **Message**: A continuous vector m_t ∈ ℝ¹⁶ transmitted by Agent_A to Agent_B each timestep.
- **Latency_Buffer**: The FIFO queue that holds outgoing messages from Agent_A and releases them to Agent_B after a fixed delay τ timesteps.
- **τ (tau)**: The integer communication latency parameter specifying how many timesteps a message is delayed before delivery to Agent_B.
- **Episode**: A single run of the simulation from reset to termination.
- **Config**: The YAML or JSON configuration file that parameterizes the Environment at initialization.
- **Observation**: The structured data returned to an agent at each timestep representing its view of the world.
- **Capture**: The event in which Agent_B occupies the same Grid position as the Target, triggering episode success.
- **Step**: One full execution of the Environment's update pipeline, advancing the simulation by one timestep.

---

## Requirements

### Requirement 1: Configuration System

**User Story:** As a researcher, I want all environment parameters defined in a single config file, so that I can reproduce and modify experiments without changing source code.

#### Acceptance Criteria

1. THE Config SHALL define the following parameters: grid width, grid height, number of obstacles, random seed, maximum steps per episode, and τ.
2. WHEN the Environment is initialized, THE Config_Loader SHALL read all parameters from the Config file before any entity is created.
3. IF the Config file is missing or malformed, THEN THE Config_Loader SHALL raise a descriptive error identifying the missing or invalid field.
4. WHEN the same Config is provided across multiple runs, THE Environment SHALL produce identical initial states (reproducibility).
5. THE Config SHALL use JSON format.

---

### Requirement 2: Grid and Coordinate Representation

**User Story:** As a developer, I want the world represented as a 2D (x, y) coordinate system, so that entity positions are explicit and independent of array indexing.

#### Acceptance Criteria

1. THE Grid SHALL be a discrete 64×64 coordinate space where valid positions are integer pairs (x, y) with 0 ≤ x < grid_width and 0 ≤ y < grid_height.
2. THE Environment SHALL store all entity positions as (x, y) coordinate pairs.
3. WHEN an entity position is queried, THE Environment SHALL return the entity's current (x, y) coordinate pair.
4. IF an operation targets a position outside the Grid bounds, THEN THE Environment SHALL reject the operation and raise a boundary violation error.

---

### Requirement 3: Entity Abstraction Layer

**User Story:** As a developer, I want a base entity abstraction, so that all world objects share a consistent interface and can be extended without modifying core logic.

#### Acceptance Criteria

1. THE Entity SHALL have a unique identifier, an (x, y) position, and a set of boolean properties: static, collidable.
2. THE Environment SHALL support the following concrete entity types derived from Entity: Agent_A, Agent_B, Obstacle, Target.
3. WHEN a new entity type is added, THE Environment SHALL require no changes to the Spatial_Index or collision logic provided the new type sets its collidable property correctly.
4. THE Target SHALL be static and non-collidable (Agent_B may occupy its position).
5. THE Obstacle SHALL be static and collidable (Agent_B may not occupy its position).

---

### Requirement 4: Spatial Indexing and Collision Detection

**User Story:** As a developer, I want a spatial index over entity positions, so that collision detection and movement validation are efficient and correct.

#### Acceptance Criteria

1. THE Spatial_Index SHALL map each occupied Grid position to the set of entities at that position.
2. WHEN an entity moves, THE Spatial_Index SHALL be updated atomically to reflect the entity's new position before any subsequent query.
3. WHEN a movement is requested to a position occupied by a collidable entity, THE Spatial_Index SHALL report a collision and THE Environment SHALL reject the movement.
4. WHEN a movement is requested to a position occupied only by non-collidable entities, THE Spatial_Index SHALL permit the movement.
5. THE Spatial_Index SHALL support lookup of all entities at a given position in O(1) average time.

---

### Requirement 5: Boundary and Validity Rules

**User Story:** As a developer, I want strict boundary enforcement, so that no entity can exist or move outside the defined Grid.

#### Acceptance Criteria

1. WHEN Agent_B attempts to move to a position outside the Grid bounds, THE Environment SHALL reject the movement and Agent_B SHALL remain at its current position.
2. WHEN the procedural generator places an entity, THE Environment SHALL verify the target position is within Grid bounds before placement.
3. IF two entities of incompatible types would occupy the same position during initialization, THEN THE Environment SHALL retry placement until a valid non-overlapping position is found.

---

### Requirement 6: Movement System

**User Story:** As a researcher, I want Agent_B to move in 8 directions including diagonals, so that the action space supports complex navigation trajectories.

#### Acceptance Criteria

1. THE Environment SHALL define Agent_B's action space as 8 discrete actions corresponding to the cardinal and diagonal directions: N, NE, E, SE, S, SW, W, NW.
2. WHEN Agent_B selects an action, THE Environment SHALL translate the action into a (Δx, Δy) displacement and compute the candidate position.
3. WHEN the candidate position is within bounds and unobstructed, THE Environment SHALL move Agent_B to the candidate position and update the Spatial_Index.
4. WHEN the candidate position is out of bounds or blocked by a collidable entity, THE Environment SHALL leave Agent_B at its current position.
5. THE Environment SHALL apply movement updates after processing communication for the current timestep.

---

### Requirement 7: Procedural Generation

**User Story:** As a researcher, I want each episode to start with a procedurally generated layout, so that agents must generalize rather than memorize fixed maps.

#### Acceptance Criteria

1. WHEN the Environment is reset, THE Procedural_Generator SHALL place Agent_A, Agent_B, the Target, and all Obstacles at valid, non-overlapping Grid positions.
2. THE Procedural_Generator SHALL use the random seed from Config to initialize its random number generator, ensuring reproducibility.
3. WHEN a fixed seed is provided, THE Environment SHALL produce the same entity layout on every reset call with that seed.
4. THE Procedural_Generator SHALL ensure Agent_B and the Target are not placed at the same initial position.
5. WHERE a minimum separation distance is specified in Config, THE Procedural_Generator SHALL enforce that Agent_B's initial position is at least that many steps from the Target.

---

### Requirement 8: Observation Interface

**User Story:** As a researcher, I want well-defined observation outputs for each agent, so that learning algorithms can consume them without environment-specific parsing.

#### Acceptance Criteria

1. WHEN observations are generated, THE Environment SHALL return Agent_A's observation as the full environment state, including all entity positions and types.
2. WHEN observations are generated, THE Environment SHALL return Agent_B's observation as an empty structure (z_B = ∅), containing no environment state information.
3. THE Environment SHALL generate observations at every timestep as part of the Step pipeline.
4. THE Environment SHALL return observations in a consistent, documented format that does not change between timesteps within an episode.
5. WHEN the Environment is reset, THE Environment SHALL return initial observations for both agents before any Step is taken.

---

### Requirement 9: Communication Interface

**User Story:** As a researcher, I want the environment to manage message passing between agents, so that the communication channel is decoupled from the learning algorithm implementations.

#### Acceptance Criteria

1. WHEN Agent_A provides a message m_t, THE Environment SHALL accept a vector of exactly 16 floating-point values.
2. IF Agent_A provides a message vector of length other than 16, THEN THE Environment SHALL raise a descriptive error.
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

### Requirement 11: Reward and Termination

**User Story:** As a researcher, I want a clear reward signal and termination condition, so that the joint reward is unambiguous and episodes end deterministically.

#### Acceptance Criteria

1. WHEN Agent_B occupies the same Grid position as the Target (Capture), THE Environment SHALL assign a positive reward to the joint reward signal.
2. WHEN Capture occurs, THE Environment SHALL set the episode status to terminated.
3. WHEN the current timestep reaches the maximum steps per episode defined in Config, THE Environment SHALL set the episode status to terminated with a reward of 0.
4. WHILE the episode is active and Capture has not occurred, THE Environment SHALL assign a reward of 0 each timestep.
5. WHEN the episode is terminated, THE Environment SHALL not process further Steps until reset.

---

### Requirement 12: Step Pipeline

**User Story:** As a developer, I want a well-defined step pipeline, so that the simulation update order is deterministic and reproducible.

#### Acceptance Criteria

1. THE Environment SHALL execute each Step in the following fixed order: (1) accept agent actions and Agent_A's message, (2) submit message to Latency_Buffer, (3) retrieve delayed message from Latency_Buffer and deliver to Agent_B, (4) apply Agent_B movement, (5) update Spatial_Index, (6) compute reward and check termination, (7) generate and return observations.
2. WHEN a Step is called on a terminated episode, THE Environment SHALL raise an error indicating the episode must be reset before stepping.
3. THE Environment SHALL increment the timestep counter by exactly 1 on each Step.

---

### Requirement 13: Reset Mechanism

**User Story:** As a developer, I want a reset method that fully reinitializes the environment, so that each episode starts from a clean, valid state.

#### Acceptance Criteria

1. WHEN reset is called, THE Environment SHALL clear all entities, reset the timestep counter to 0, and clear the Latency_Buffer.
2. WHEN reset is called, THE Environment SHALL invoke the Procedural_Generator to place all entities at new valid positions.
3. WHEN reset is called, THE Environment SHALL return initial observations for both agents.
4. WHEN reset is called with a new seed, THE Environment SHALL use that seed for the subsequent episode's procedural generation.

---

### Requirement 14: Debugging and Logging

**User Story:** As a developer, I want logging and optional visualization tools, so that I can inspect environment state and diagnose issues during development.

#### Acceptance Criteria

1. THE Environment SHALL log entity positions, movement outcomes, and collision events at a configurable verbosity level.
2. WHERE the debug module is enabled, THE Environment SHALL render a text-based representation of the Grid showing entity positions at each timestep.
3. THE Environment SHALL expose a method to dump the full current state as a structured dictionary for external inspection.

---

### Requirement 15: Extensibility

**User Story:** As a researcher, I want the environment to be extensible, so that new entity types, grid sizes, and generation strategies can be added without restructuring core modules.

#### Acceptance Criteria

1. THE Environment SHALL read grid dimensions exclusively from Config, with no hardcoded size values in environment logic.
2. WHEN a new Entity subclass is introduced, THE Environment SHALL require no changes to the Step pipeline or Spatial_Index provided the subclass implements the Entity interface.
3. THE Environment SHALL remain fully independent of any learning algorithm, neural network, or optimizer code.
4. WHERE an alternative procedural generation strategy is provided, THE Environment SHALL accept it as a configurable parameter without modifying core environment logic.
