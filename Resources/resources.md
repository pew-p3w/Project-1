# Resources

Reference materials for the Emergent Communication in Asymmetric Dec-POMDPs project.

## Foundational Papers

- **Dec-POMDP Framework**: Bernstein et al. (2002) — "The Complexity of Decentralized Control of Markov Decision Processes"
- **Emergent Communication**: Lazaridou & Baroni (2020) — "Emergent Multi-Agent Communication in the Deep Learning Era"
- **DIAL / CommNet**: Foerster et al. (2016) — "Learning to Communicate with Deep Multi-Agent Reinforcement Learning"
- **MADDPG**: Lowe et al. (2017) — "Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments"

## Relevant Concepts

- **Dec-POMDP**: Decentralized Partially Observable Markov Decision Process — the formal framework used in this project
- **Asymmetric Observability**: Agent A sees the full continuous world state; Agent B sees nothing — the core setup here
- **Emergent Communication**: Communication protocols that arise from training rather than being hand-designed
- **Network Latency (τ)**: Artificial delay introduced to the message channel to study robustness of learned representations
- **Continuous Physics**: Agent B moves with velocity-based steering in a 2D world with geometric obstacles, using pymunk for collision detection

## Similar Environments

- **OpenAI Multiagent Particle Environments** — continuous 2D multi-agent environments with communication
- **MuJoCo / dm_control** — continuous physics simulation for RL
- **Pygame + pymunk demos** — 2D physics sandbox environments

## Project Documents

- `project.tex` — Formal problem formulation (LaTeX)
- `.kiro/specs/dec-pomdp-environment/requirements.md` — Environment requirements
- `.kiro/specs/dec-pomdp-environment/design.md` — Technical design
- `.kiro/specs/dec-pomdp-environment/tasks.md` — Implementation task list

## Tools & Libraries

- **Python** — Primary implementation language
- **pymunk** — 2D physics library (Chipmunk-based) for collision detection and response
- **Pygame** — Rendering and visualization
- **hypothesis** — Property-based testing library
- **pytest** — Test runner
- **PyTorch** — Neural network framework (future agent implementation)
