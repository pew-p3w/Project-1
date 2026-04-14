# Environment Configuration Guide

All environment parameters are controlled through `Config/config.json`. No code changes needed — just edit the JSON and re-run.

---

## Full Parameter Reference

### World

| Parameter | Type | Required | Description |
|---|---|---|---|
| `world_width` | float | yes | Width of the 2D world in units (e.g. 800.0) |
| `world_height` | float | yes | Height of the 2D world in units (e.g. 600.0) |

The world is bounded by solid walls on all four edges. Agent B cannot leave.

---

### Physics & Agent B Movement

| Parameter | Type | Required | Description |
|---|---|---|---|
| `agent_radius` | float | yes | Radius of Agent B's circular collision body. Larger = harder to navigate tight spaces |
| `max_speed` | float | yes | Maximum speed Agent B can reach (world units per step). Higher = faster agent |
| `max_angular_velocity` | float | yes | Maximum heading change per step in radians. Lower = less agile, more realistic turning |
| `capture_radius` | float | yes | How close Agent B must get to the target to capture it. Larger = easier to capture |

**Tuning tips:**
- Increase `max_angular_velocity` for a more agile agent, decrease for a more realistic vehicle-like turning radius
- `capture_radius` defines the yellow circle around the target in the renderer — Agent B wins when it enters that circle

---

### Episode

| Parameter | Type | Required | Description |
|---|---|---|---|
| `random_seed` | int | yes | Seed for reproducible world generation. Change to get a different layout |
| `max_steps` | int | yes | Maximum steps per episode before timeout. Increase for longer episodes |
| `tau` | int | yes | Communication latency in timesteps. Agent B receives messages `tau` steps late |

**Tuning tips:**
- `tau = 0` — no delay, Agent B gets messages instantly (easiest)
- `tau = 3` — 3-step delay (default, moderate difficulty)
- `tau = 10+` — high latency, very challenging coordination

---

### Spawn Constraints

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `min_separation` | float | no | 0.0 | Minimum Euclidean distance between Agent B and the target at spawn. Prevents trivially easy episodes |

---

### Obstacles

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `obstacles` | list | no | `[]` | List of explicit obstacle definitions (see shapes below) |
| `procedural` | object | no | `null` | Procedural obstacle generation settings (see below) |

If both are empty, the world has no obstacles — just open space.

---

### Rendering & Debug

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `render` | bool | no | `false` | Set to `true` to open the Pygame window and watch the simulation live |
| `log_level` | str | no | `"INFO"` | Logging verbosity: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"` |
| `message_dim` | int | no | `16` | Dimension of the communication message vector. Keep at 16 unless you know what you're doing |

---

## Obstacle Shapes

### Rectangular Wall

Defined by centre position, size, and rotation angle.

```json
{
  "type": "rect",
  "cx": 400.0,
  "cy": 300.0,
  "width": 200.0,
  "height": 20.0,
  "angle": 0.0
}
```

| Field | Description |
|---|---|
| `cx`, `cy` | Centre position of the rectangle |
| `width` | Width of the rectangle (must be > 0) |
| `height` | Height of the rectangle (must be > 0) |
| `angle` | Rotation in radians (0.0 = horizontal) |

Rendered as a red rectangle.

---

### Circular Pillar

Defined by centre position and radius.

```json
{
  "type": "circle",
  "cx": 300.0,
  "cy": 200.0,
  "radius": 40.0
}
```

| Field | Description |
|---|---|
| `cx`, `cy` | Centre position of the circle |
| `radius` | Radius of the pillar (must be > 0) |

Rendered as an orange circle.

---

### Convex Polygon

Defined by an ordered list of vertices. Must be convex (no concave shapes).

```json
{
  "type": "polygon",
  "vertices": [
    [100.0, 100.0],
    [150.0, 80.0],
    [180.0, 130.0],
    [120.0, 150.0]
  ]
}
```

| Field | Description |
|---|---|
| `vertices` | List of `[x, y]` coordinate pairs. Minimum 3 points. Must form a convex shape |

Rendered as a purple polygon.

---

## Procedural Obstacle Generation

Instead of defining obstacles manually, let the environment generate random circle obstacles each episode.

```json
{
  "obstacles": [],
  "procedural": {
    "count": 8,
    "min_radius": 10.0,
    "max_radius": 30.0
  }
}
```

| Field | Description |
|---|---|
| `count` | Number of obstacles to generate per episode |
| `min_radius` | Minimum radius of generated circle obstacles |
| `max_radius` | Maximum radius of generated circle obstacles |

Obstacles are placed randomly each episode using `random_seed` for reproducibility.

---

## Example Configurations

### Open World (no obstacles)

```json
{
  "world_width": 800.0,
  "world_height": 600.0,
  "agent_radius": 10.0,
  "max_speed": 150.0,
  "max_angular_velocity": 0.2,
  "capture_radius": 20.0,
  "random_seed": 42,
  "max_steps": 500,
  "tau": 3,
  "obstacles": [],
  "render": true,
  "log_level": "INFO"
}
```

---

### Corridor / Maze Layout

Two vertical walls creating a corridor Agent B must navigate through.

```json
{
  "world_width": 800.0,
  "world_height": 600.0,
  "agent_radius": 10.0,
  "max_speed": 150.0,
  "max_angular_velocity": 0.2,
  "capture_radius": 20.0,
  "random_seed": 42,
  "max_steps": 500,
  "tau": 3,
  "min_separation": 100.0,
  "obstacles": [
    {"type": "rect", "cx": 300.0, "cy": 200.0, "width": 20.0, "height": 300.0, "angle": 0.0},
    {"type": "rect", "cx": 500.0, "cy": 400.0, "width": 20.0, "height": 300.0, "angle": 0.0}
  ],
  "render": true,
  "log_level": "INFO"
}
```

---

### Pillar Field

Multiple circular pillars scattered across the world.

```json
{
  "world_width": 800.0,
  "world_height": 600.0,
  "agent_radius": 10.0,
  "max_speed": 150.0,
  "max_angular_velocity": 0.2,
  "capture_radius": 20.0,
  "random_seed": 42,
  "max_steps": 500,
  "tau": 3,
  "obstacles": [
    {"type": "circle", "cx": 200.0, "cy": 150.0, "radius": 30.0},
    {"type": "circle", "cx": 400.0, "cy": 300.0, "radius": 25.0},
    {"type": "circle", "cx": 600.0, "cy": 150.0, "radius": 30.0},
    {"type": "circle", "cx": 200.0, "cy": 450.0, "radius": 25.0},
    {"type": "circle", "cx": 600.0, "cy": 450.0, "radius": 30.0}
  ],
  "render": true,
  "log_level": "INFO"
}
```

---

### Procedural Random World

New random obstacle layout every episode.

```json
{
  "world_width": 800.0,
  "world_height": 600.0,
  "agent_radius": 10.0,
  "max_speed": 150.0,
  "max_angular_velocity": 0.2,
  "capture_radius": 20.0,
  "random_seed": 42,
  "max_steps": 500,
  "tau": 3,
  "min_separation": 80.0,
  "obstacles": [],
  "procedural": {"count": 8, "min_radius": 10.0, "max_radius": 35.0},
  "render": true,
  "log_level": "INFO"
}
```

---

### High Latency Challenge

Crank up `tau` to make coordination much harder.

```json
{
  "world_width": 800.0,
  "world_height": 600.0,
  "agent_radius": 10.0,
  "max_speed": 100.0,
  "max_angular_velocity": 0.15,
  "capture_radius": 25.0,
  "random_seed": 42,
  "max_steps": 1000,
  "tau": 10,
  "min_separation": 150.0,
  "obstacles": [],
  "procedural": {"count": 5, "min_radius": 15.0, "max_radius": 40.0},
  "render": true,
  "log_level": "INFO"
}
```

---

## Renderer Colour Key

| Colour | Entity |
|---|---|
| Blue circle | Agent B (the actor) |
| Green circle (top-left) | Agent A (the observer) |
| Yellow circle | Target + capture zone |
| Red rectangle | Rectangular wall obstacle |
| Orange circle | Circular pillar obstacle |
| Purple polygon | Polygon obstacle |

---

## Running the Demo

```bash
# Make sure render is set to true in Config/config.json
.venv/bin/python jobs/demo.py
```

Agent B moves with random actions until you close the window or press Ctrl+C.
