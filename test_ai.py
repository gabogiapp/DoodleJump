import gymnasium as gym
from stable_baselines3 import PPO
from gymnasium_env_doodle.envs.doodle_env import DoodleJumpEnv
import pygame
import sys

def test():
    pygame.init()
    WIDTH, HEIGHT = 448, 682
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("AI Testing")
    clock = pygame.time.Clock()

    # Match the environment settings used in training
    env = DoodleJumpEnv(width=WIDTH, height=HEIGHT, enable_hazards=False, enable_powerups=False)

    try:
        # Load the updated v13 model
        model = PPO.load("ppo_doodle_jump_stage1_v15")
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    obs, info = env.reset()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # AI INFERENCE
        action, _states = model.predict(obs, deterministic=True)

        # ENVIRONMENT STEP
        obs, reward, terminated, truncated, info = env.step(action)

        if terminated or truncated:
            obs, info = env.reset()

        # DRAWING
        screen.fill((250, 248, 239))
        for p in env.platforms: p.draw(screen)
        env.player.draw(screen)

        # Show Score
        font = pygame.font.SysFont("Arial", 18, bold=True)
        txt = font.render(f"AI SCORE: {int(info['score'])}", True, (50, 50, 50))
        screen.blit(txt, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    test()
