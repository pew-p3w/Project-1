# Environment Task

## 1. Project Environment Setup
- Create a virtual environment and manage dependencies
- Decide on configuration format (YAML or JSON) and include a parser library if needed
- Establish a clear folder structure separating environment logic, utilities, and configuration

## 2. Core Python Modules
Define the essential modules:
- `environment.py` — world management and simulation loop
- `entity.py` — base object definitions
- `agent.py` — agent-specific behavior placeholders
- `objects.py` — walls, obstacles, and targets
- `spatial.py` — position tracking and collision logic
- `config_loader.py` — reads environment settings from config file
- `debug.py` *(optional)* — visualization and inspection utilities

## 3. Configuration File System
Create a config file defining:
- Grid size (width and height)
- Number of agents
- Number of walls and obstacles
- Target count
- Random seed
- Maximum steps per episode
- Communication latency parameter `τ`

All parameters must be read from this file at initialization.

## 4. Coordinate-Based World Representation
- Define the environment as a 2D `(x, y)` coordinate system (not a grid array)
- All entities store positions as `(x, y)` coordinates
- Support dynamic placement and movement without relying on fixed grid cells

## 5. Entity Abstraction Layer
Implement a base entity with:
- Unique identity
- Position in coordinate space
- Optional properties: static, movable, collidable

Extend this for all objects: agents, walls, obstacles, and target.

## 6. Environment State Management
The environment must track:
- A collection of all entities
- Separate tracking for agents
- Current timestep
- Episode active/terminated status

## 7. Spatial Indexing System
Implement a structure to efficiently map positions to entities, supporting:
- Fast lookup of what exists at a position
- Collision detection
- Movement validation
- Quick updates as entities move

## 8. Boundary and Validity Rules
- Enforce grid boundaries
- Define which entities block movement
- Prevent invalid overlaps at initialization and during movement
- Optionally allow multiple entities per position depending on type

## 9. Movement System
- Specify action space including diagonal movement (8-directional for Agent B)
- Define how actions translate into coordinate changes
- Enforce collision and boundary constraints
- Update spatial index after each movement

## 10. Procedural Generation System
- Randomly generate valid positions for all entities
- Avoid incorrect overlaps during placement
- Optionally enforce minimum distance between agent and target
- Ensure reproducibility via fixed seed

## 11. Observation Interface
- Agent A: receives full environment state `z_A = s`
- Agent B: receives no environment state `z_B = ∅` (blind to world)
- Generate observations at every timestep in a consistent format

## 12. Communication Interface (Environment Side)
Provide hooks for:
- Sending messages from Agent A (`m_t ∈ ℝ¹⁶`)
- Delivering messages to Agent B
- Integrating with the latency buffer

The environment manages *when* messages are passed, not *how* they are generated.

## 13. Latency Buffer
Implement delayed message delivery:
- Store outgoing messages in a buffer
- Release messages after fixed delay `τ`
- Handle empty buffer cases at early timesteps

## 14. Reward and Termination Conditions
- Detect when the target is captured
- Assign rewards accordingly
- End episode on success or step limit reached

## 15. Environment Step Pipeline
Full update cycle per timestep:
1. Accept agent actions
2. Process communication
3. Apply movement updates
4. Update environment state
5. Compute rewards
6. Generate observations
7. Check termination

## 16. Reset Mechanism
- Clear all entities
- Regenerate the environment (procedural generation)
- Reset timestep counter
- Return initial observations

## 17. Debugging and Logging Tools
- Log entity positions
- Log movement and interactions
- Optional text-based visualization of the coordinate space

## 18. Testing Requirements
Verify correctness of:
- Valid entity initialization
- Boundary enforcement
- Collision handling
- Correct movement updates
- Message delay behavior
- Reproducibility with fixed seeds

## 19. Extensibility Design
- Allow easy addition of new entity types
- Allow grid size changes via config
- Support different procedural generation strategies
- Keep environment fully independent from learning algorithms
