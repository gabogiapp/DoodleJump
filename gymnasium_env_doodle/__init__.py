from gymnasium.envs.registration import register

register(
    id="gymnasium_env_doodle/GridWorld-v0",
    entry_point="gymnasium_env_doodle.envs:GridWorldEnv",
)
