"""Demo script: run the Dec-POMDP environment with random actions and Pygame rendering.

Usage:
    .venv/bin/python jobs/demo.py

Controls:
    Close the window to exit.
"""
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.environment import DecPOMDPEnvironment

def main():
    env = DecPOMDPEnvironment("Config/config.json")
    obs_a, obs_b = env.reset()
    print(f"Environment ready. World: {env._config.world_width}x{env._config.world_height}")
    print(f"Agent B start: {obs_a['agent_b']}, Target: {obs_a['target']}")

    episode = 0
    step_count = 0

    try:
        while True:
            # Random steering action
            delta_heading = random.uniform(-env._config.max_angular_velocity,
                                           env._config.max_angular_velocity)
            delta_speed = random.uniform(-10.0, 20.0)
            message = [random.gauss(0, 1) for _ in range(16)]

            result = env.step((delta_heading, delta_speed), message)
            step_count += 1

            if result.terminated:
                episode += 1
                reward_str = "CAPTURED!" if result.reward > 0 else "timeout"
                print(f"Episode {episode} ended ({reward_str}) after {step_count} steps")
                step_count = 0
                # Use a different seed each episode so procedural generation
                # produces a fresh layout every time
                obs_a, obs_b = env.reset(seed=episode)
    except KeyboardInterrupt:
        print("Demo stopped.")
    finally:
        env.close()

if __name__ == "__main__":
    main()
