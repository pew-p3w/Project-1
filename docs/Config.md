# Environment Configuration Guide

All environment parameters are controlled through `Config/config.json`. This guide describes the available settings for the Multi-Agent Target Capture environment.

---

## Full Parameter Reference

### World

| Parameter | Type | Required | Description |
|---|---|---|---|
| `world_width` | float | yes | Width of the 2D world in units |
| `world_height` | float | yes | Height of the 2D world in units |

---

### Catcher Agents

Both agents (A and B) share these physical properties.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `agent_radius` | float | yes | Radius of the agent's circular body |
| `max_speed` | float | yes | Maximum speed an agent can reach |
| `max_angular_velocity` | float | yes | Maximum rate of change for heading (radians/step) |
| `capture_radius` | float | yes | Distance threshold for a successful capture |

### Ray-Casting Observations

| Parameter | Type | Required | Description |
|---|---|---|---|
| `num_rays` | int | yes | Number of rays cast by each agent |
| `ray_length` | float | yes | Maximum distance a ray can travel |
| `fov` | float | yes | Field of view in radians (e.g., `2 * pi` for 360 degrees) |

---

### Moving Target

The target is dynamic and attempts to evade the catchers.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `target_radius` | float | yes | Radius of the target's circular body |
| `target_max_speed` | float | yes | Maximum speed of the target (usually > `max_speed`) |
| `target_strategy` | str | no | Strategy for evasion (e.g., `"reactive"`, `"random"`) |

---

### Communication & Episode

| Parameter | Type | Required | Description |
|---|---|---|---|
| `random_seed` | int | yes | Seed for reproducible generation |
| `max_steps` | int | yes | Maximum steps per episode |
| `tau` | int | yes | Communication latency (timesteps) |
| `message_dim` | int | no | Dimension of the communication vector (default: 8) |

---

### Obstacles

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `obstacles` | list | no | `[]` | List of explicit obstacle definitions |
| `procedural` | object | no | `null` | Procedural generation settings |

---

### Rendering & Debug

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `render` | bool | no | `false` | Enable live Pygame visualization |
| `log_level` | str | no | `"INFO"` | Logging verbosity |

---

## Obstacle Shapes

The environment supports `rect`, `circle`, and `polygon` obstacle types. See the design document for detailed geometry definitions.

---

## Example Configuration

```json
{
  "world_width": 800.0,
  "world_height": 600.0,
  "agent_radius": 15.0,
  "max_speed": 100.0,
  "max_angular_velocity": 0.2,
  "num_rays": 32,
  "ray_length": 400.0,
  "fov": 6.28,
  "target_radius": 10.0,
  "target_max_speed": 120.0,
  "capture_radius": 25.0,
  "random_seed": 42,
  "max_steps": 1000,
  "tau": 2,
  "message_dim": 8,
  "render": true,
  "log_level": "INFO"
}
```

---

## Renderer Colour Key

| Colour | Entity |
|---|---|
| Blue circle | Agent A |
| Cyan circle | Agent B |
| Green circle | Target |
| Yellow circle | Capture Zone (around Target) |
| Red/Purple | Obstacles |
| White lines | Ray-casts (optional debug view) |
