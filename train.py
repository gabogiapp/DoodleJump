import gymnasium as gym
from stable_baselines3 import PPO
from gymnasium_env_doodle.envs.doodle_env import DoodleJumpEnv

def train():
    # 1. Create the Environment
    # We keep hazards and powerups off for Stage 1 (Basic Climbing)
    env = DoodleJumpEnv(
        width=448,
        height=682,
        enable_hazards=False,
        enable_powerups=False
    )

    # 2. Initialize the Model
    # MultiInputPolicy is required because our observation space is a Dict
    model = PPO(
        "MultiInputPolicy",
        env,
        verbose=1,
        ent_coef=0.025,
        learning_rate=0.0002,
        tensorboard_log="./ppo_doodle_tensorboard/"
    )

    # 3. Train the AI
    # We use 600,000 steps to give it time to learn the 'next_platform' logic
    model.learn(total_timesteps=4000000)

    # 4. Save the Model
    # Saved as v13 to distinguish it from the older, stalling versions
    model.save("ppo_doodle_jump_stage1_v15")
if __name__ == "__main__":
    train()
