from enum import Enum
import math
import random
import gymnasium as gym
from gymnasium import spaces
import pygame
import numpy as np
from game import Player, Projectile, Platform, Monster, BlackHole

class Action(Enum):
    right = 0
    left = 1
    shoot = 2
    stay = 3

class DoodleJumpEnv(gym.Env):
    def __init__(self, width=448, height=682, enable_hazards=False, enable_powerups=False):
        super().__init__()
        self.width = width
        self.height = height
        self.enable_hazards = enable_hazards
        self.enable_powerups = enable_powerups

        self.max_patience = 240
        self.patience_timer = self.max_patience
        self.max_score = 0
        self.last_action = 3

        # New tracking variables initialization
        self.max_height = 0
        self.stagnation_timer = 0
        self.visited_platforms = set()

        self.action_space = spaces.Discrete(4)

        # Updated to 10 closest platforms (x, y, type) = 30 values
        self.observation_space = spaces.Dict({
            "player": spaces.Box(low=-1, high=1, shape=(5,), dtype=np.float32),
            "platforms": spaces.Box(low=-1, high=1, shape=(30,), dtype=np.float32),
            "hazard": spaces.Box(low=-1, high=1, shape=(2,), dtype=np.float32),
            "timer": spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32)
        })

    def _get_obs(self, active_plats=None):
        obs = {
            "player": np.array([
                self.player.rect.centerx / self.width,
                self.player.rect.centery / self.height,
                self.player.vel_x / self.player.max_vel_x,
                self.player.vel_y / 20.0,
                1.0 if self.player.powerup_timer > 0 else 0.0
            ], dtype=np.float32),
            "timer": np.array([self.patience_timer / self.max_patience], dtype=np.float32)
        }

        # If no specific platforms provided (like in reset), find 10 closest overall
        if active_plats is None:
            platform_distances = []
            for p in self.platforms:
                dist = math.sqrt((self.player.rect.centerx - p.rect.centerx)**2 +
                                 (self.player.rect.centery - p.rect.centery)**2)
                platform_distances.append((dist, p))
            active_plats = [p for dist, p in sorted(platform_distances, key=lambda x: x[0])[:10]]

        plat_data = []
        for p in active_plats:
            rel_x = (p.rect.centerx - self.player.rect.centerx) / self.width
            rel_y = (p.rect.centery - self.player.rect.centery) / self.height
            type_idx = {'green': 0, 'blue': 1, 'white': 2, 'red': 3}.get(p.type, 0) / 3.0
            plat_data.extend([rel_x, rel_y, type_idx])

        # Pad to 30 values (10 platforms * 3 features)
        while len(plat_data) < 30:
            plat_data.extend([0.0, -1.0, 0.0])

        obs["platforms"] = np.array(plat_data, dtype=np.float32)

        hazards = self.monsters + self.black_holes
        if hazards:
            closest_h = min(hazards, key=lambda h: math.dist(self.player.rect.center,
                        (h.rect.center if hasattr(h, 'rect') else h.center)))
            h_center = closest_h.rect.center if hasattr(closest_h, 'rect') else closest_h.center
            obs["hazard"] = np.array([
                (h_center[0] - self.player.rect.centerx) / self.width,
                (h_center[1] - self.player.rect.centery) / self.height
            ], dtype=np.float32)
        else:
            obs["hazard"] = np.array([0.0, -1.0], dtype=np.float32)

        return obs

    def _get_info(self):
        return {"score": self.player.score}

    def _update_game_logic(self):
        self.player.move(keys=None)

        if self.player.rect.y < self.height // 2:
            diff = self.height // 2 - self.player.rect.y
            self.player.rect.y = self.height // 2
            self.player.score += diff
            for p in self.platforms: p.rect.y += diff
            for m in self.monsters: m.update(); m.rect.y += diff
            for b in self.bullets: b.update(); b.rect.y += diff
            for bh in self.black_holes: bh.center[1] += diff

        for p in self.platforms: p.update()

        self.platforms = [p for p in self.platforms if p.rect.top < self.height]
        self.monsters = [m for m in self.monsters if m.rect.top < self.height]
        self.black_holes = [bh for bh in self.black_holes if bh.center[1] - bh.radius < self.height]

        while len(self.platforms) < 15:
            highest_y = min([p.rect.y for p in self.platforms])
            new_y = highest_y - random.randint(80, 110)
            new_plat = Platform(new_y, self.player.score)
            self.platforms.append(new_plat)

        for p in self.platforms:
            if self.player.rect.colliderect(p.rect) and self.player.vel_y > 0:
                if self.player.rect.bottom <= p.rect.centery + 10:
                    self.player.rect.bottom = p.rect.top
                    self.player.vel_y = self.player.jump_power
                    if p.type == 'white': self.platforms.remove(p)
                    break

    def step(self, action):
        # 1. Action execution
        if action == 0: self.player.vel_x += self.player.accel_x
        elif action == 1: self.player.vel_x -= self.player.accel_x
        elif action == 3: self.player.vel_x *= 0.85

        jitter_penalty = -1.0 if (action == 0 and self.last_action == 1) or \
                                (action == 1 and self.last_action == 0) else 0.0
        self.last_action = action

        old_vel_y = self.player.vel_y
        self._update_game_logic()

        reward = jitter_penalty
        terminated = False
        truncated = False

        # --- 2. ALTITUDE PROGRESS LOGIC ---
        if self.player.rect.centery < self.max_height:
            height_diff = self.max_height - self.player.rect.centery
            reward += height_diff * 15.0
            self.max_height = self.player.rect.centery
            self.stagnation_timer = 0
        else:
            self.stagnation_timer += 1
            reward -= 0.1

        # --- 3. CLOSEST PLATFORMS & NOVELTY JUMP REWARD ---
        platform_distances = []
        for p in self.platforms:
            dist = math.sqrt((self.player.rect.centerx - p.rect.centerx)**2 +
                             (self.player.rect.centery - p.rect.centery)**2)
            platform_distances.append((dist, p))

        sorted_by_dist = sorted(platform_distances, key=lambda x: x[0])
        closest_10_platforms = [p for dist, p in sorted_by_dist[:10]]

        for p in closest_10_platforms:
            if self.player.rect.colliderect(p.rect) and old_vel_y > 0:
                p_id = id(p)
                if p_id not in self.visited_platforms:
                    self.visited_platforms.add(p_id)
                    reward += 50.0
                else:
                    reward -= 5.0
                break

        # --- 4. STAGNATION DEATH ---
        STAGNATION_LIMIT = 500
        if self.stagnation_timer > STAGNATION_LIMIT:
            reward -= 100.0
            terminated = True

        # --- 5. TERMINATION ---
        if self.player.rect.top > self.height:
            reward -= 200.0
            terminated = True

        return self._get_obs(closest_10_platforms), reward, terminated, truncated, self._get_info()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.player = Player()
        self.max_score = 0
        self.last_action = 3

        # Reset tracking variables
        self.max_height = self.player.rect.centery
        self.stagnation_timer = 0
        self.visited_platforms = set()

        self.platforms = [Platform(self.height - 50, 0)]
        self.platforms[0].rect.x, self.platforms[0].rect.width = 0, self.width
        self.platforms[0].type = 'green'

        self.monsters, self.black_holes, self.bullets = [], [], []
        for i in range(1, 15):
            self.platforms.append(Platform(self.height - i*70, 0))

        self.patience_timer = self.max_patience
        return self._get_obs(), self._get_info()
