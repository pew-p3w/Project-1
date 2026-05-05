# Catcher Agents

In theis setup, we have two agents A and Agent B are **Catchers**. They are symmetrical in their capabilities and must work together to capture the faster moving target.

## Role

- **Active Pursuit**: Both agents move continuously through the 2D physics world.
- **Coordination**: They must use their communication channel to share information and coordinate a capture strategy.
- **Capture**: The episode succeeds when either agent (or their combined effort) results in an agent being within the `capture_radius` of the target.

## Observability

Each agent has its own local, partially observable view of the world:

### Ray-Casting
Agents "see" using a set of rays projected from their center. 
- **Input**: Distance and object type for each ray.
- **Occlusion**: Rays are blocked by obstacles, the other agent, and world boundaries.
- **Field of View**: Configurable (e.g., 360 degrees or a forward-facing cone).

### Communication
- Receives a message vector from the other agent.
- Messages may be delayed by a configurable latency $\tau$.

## Movement

Agents use a continuous action space for movement
- **Thrust**: Forward force.
- **Steering**: change in heading.

Physics is handled by `pymunk`, ensuring realistic collisions and momentum.

## Action Space

1. **Movement Actions**: `(thrust, steering)`
2. **Communication Actions**: A vector of floats representing the message to be sent to the other agent.

## Interface (PettingZoo)

Agents are identified by strings (`"catcher_0"`, `"catcher_1"`) and interact via the standard PettingZoo `step()` and `observe()` methods.
