import pygame
import sys
import random
import math

# --- CONFIGURATION ---
RENDER = True
RESOLUTION = WIDTH, HEIGHT = 448, 682
TITLE = "Doodle Jump"
FPS = 60

# FEATURE FLAGS
ENABLE_MONSTERS = False
ENABLE_BLACK_HOLES = False
ENABLE_POWERUPS = False

# Colors
BACKGROUND = (250, 248, 239)
PLAT_GREEN, PLAT_BLUE = (63, 255, 63), (127, 191, 255)
PLAT_WHITE = (255, 255, 255)
MONSTER_COLOR = (138, 43, 226)
BLACK_HOLE_COLOR = (20, 20, 20)
BULLET_COLOR = (255, 50, 50)

# --- CLASSES ---

class Projectile:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 6, 12)
        self.speed = -15

    def update(self):
        self.rect.y += self.speed

    def draw(self, surface):
        pygame.draw.rect(surface, BULLET_COLOR, self.rect)

class Player:
    def __init__(self):
        self.width, self.height = 30, 30
        self.rect = pygame.Rect(WIDTH//2, HEIGHT-100, self.width, self.height)
        self.vel_y = 0
        self.vel_x = 0
        self.max_vel_x = 7
        self.accel_x = 0.8
        self.gravity = 0.35
        self.jump_power = -11
        self.score = 0
        self.powerup_timer = 0
        self.shoot_cooldown = 0

    def move(self, keys=None):
        if keys is not None:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.vel_x -= self.accel_x
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.vel_x += self.accel_x
            else: self.vel_x *= 0.85
        else:
            self.vel_x *= 0.85

        self.vel_x = max(-self.max_vel_x, min(self.max_vel_x, self.vel_x))
        self.rect.x += self.vel_x
        if self.rect.right < 0: self.rect.left = WIDTH
        elif self.rect.left > WIDTH: self.rect.right = 0

        if self.powerup_timer > 0:
            self.vel_y = -18
            self.powerup_timer -= 1
        else:
            self.vel_y += self.gravity

        self.rect.y += self.vel_y
        if self.shoot_cooldown > 0: self.shoot_cooldown -= 1

    def draw(self, surface):
        color = (255, 215, 0) if self.powerup_timer > 0 else (255, 255, 0)
        pygame.draw.rect(surface, color, self.rect)
        if self.powerup_timer > 0:
            pygame.draw.rect(surface, (0, 200, 255), self.rect, 3)
        pygame.draw.rect(surface, (0,0,0), self.rect, 2)
        pygame.draw.rect(surface, (0,0,0), (self.rect.centerx-2, self.rect.top-8, 4, 8))

class Platform:
    def __init__(self, y, score):
        self.width, self.height = 60, 12
        self.rect = pygame.Rect(random.randint(0, WIDTH-self.width), y, self.width, self.height)

        # Generation Logic: Only Green, Blue, and White
        if score < 1000:
            self.type = 'green'
        else:
            self.type = random.choice(['green', 'green', 'blue', 'white'])

        self.vel_x = random.choice([-2, 2]) if self.type == 'blue' else 0
        self.has_item = None

        if ENABLE_POWERUPS:
            item_roll = random.random()
            if item_roll < 0.01: self.has_item = 'rocket'
            elif item_roll < 0.025: self.has_item = 'propeller'
            elif item_roll < 0.05: self.has_item = 'spring'

    def update(self):
        if self.type == 'blue':
            self.rect.x += self.vel_x
            if self.rect.left < 0 or self.rect.right > WIDTH: self.vel_x *= -1

    def draw(self, surface):
        color = {'green': PLAT_GREEN, 'blue': PLAT_BLUE, 'white': PLAT_WHITE}[self.type]
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (0,0,0), self.rect, 1)
        if self.has_item == 'spring':
            pygame.draw.rect(surface, (100,100,100), (self.rect.centerx-6, self.rect.top-10, 12, 10))
        elif self.has_item == 'rocket':
            pygame.draw.polygon(surface, (255, 0, 0), [(self.rect.centerx, self.rect.top-25), (self.rect.centerx-10, self.rect.top), (self.rect.centerx+10, self.rect.top)])
        elif self.has_item == 'propeller':
            pygame.draw.circle(surface, (0, 100, 255), (self.rect.centerx, self.rect.top-8), 8)

class Monster:
    def __init__(self, y):
        self.width, self.height = 45, 45
        self.rect = pygame.Rect(random.randint(0, WIDTH-self.width), y, self.width, self.height)
        self.vel_x = random.choice([-3, 3])

    def update(self):
        self.rect.x += self.vel_x
        if self.rect.left < 0 or self.rect.right > WIDTH: self.vel_x *= -1

    def draw(self, surface):
        pygame.draw.ellipse(surface, MONSTER_COLOR, self.rect)
        pygame.draw.circle(surface, (255,255,255), (self.rect.x+12, self.rect.y+15), 6)
        pygame.draw.circle(surface, (255,255,255), (self.rect.x+33, self.rect.y+15), 6)

class BlackHole:
    def __init__(self, y):
        self.center = [random.randint(50, WIDTH-50), y]
        self.radius = 35

    def draw(self, surface):
        pygame.draw.circle(surface, BLACK_HOLE_COLOR, self.center, self.radius)
        pygame.draw.circle(surface, (50, 50, 50), self.center, self.radius, 3)

# --- ENGINE ---

def run_game(screen, clock):
    player = Player()
    platforms = [Platform(HEIGHT - 50, 0)]
    platforms[0].rect.x, platforms[0].rect.width = 0, WIDTH
    platforms[0].type = 'green'

    monsters, black_holes, bullets = [], [], []

    # Initial generation
    for i in range(1, 15):
        platforms.append(Platform(HEIGHT - i*70, 0))

    running = True
    while running:
        if RENDER:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None # Signal to exit program entirely

        keys = pygame.key.get_pressed()
        player.move(keys)

        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and player.shoot_cooldown == 0:
            bullets.append(Projectile(player.rect.centerx - 3, player.rect.top))
            player.shoot_cooldown = 12

        # Camera scroll & Height-based Score
        if player.rect.y < HEIGHT // 2:
            diff = HEIGHT // 2 - player.rect.y
            player.rect.y = HEIGHT // 2
            player.score += diff # Score tied directly to height climbed
            for p in platforms: p.rect.y += diff
            for m in monsters: m.rect.y += diff
            for b in bullets: b.rect.y += diff
            for bh in black_holes: bh.center[1] += diff

        # Update & Cleanup
        for b in bullets[:]:
            b.update()
            if b.rect.bottom < 0: bullets.remove(b)

        for p in platforms: p.update()
        for m in monsters: m.update()

        platforms = [p for p in platforms if p.rect.top < HEIGHT]
        monsters = [m for m in monsters if m.rect.top < HEIGHT]
        black_holes = [bh for bh in black_holes if bh.center[1] - bh.radius < HEIGHT]

        # SPAWN logic
        while len(platforms) < 15:
            highest_y = min([p.rect.y for p in platforms])
            new_y = highest_y - random.randint(80, 110)
            new_plat = Platform(new_y, player.score)
            platforms.append(new_plat)

            if ENABLE_MONSTERS and random.random() < 0.07:
                monsters.append(Monster(new_y - 50))
            if ENABLE_BLACK_HOLES and random.random() < 0.03:
                black_holes.append(BlackHole(new_y - 90))

        # Collisions
        for p in platforms:
            if player.rect.colliderect(p.rect) and player.vel_y > 0:
                if player.rect.bottom <= p.rect.centery + 10:
                    player.rect.bottom = p.rect.top
                    player.vel_y = player.jump_power
                    if p.has_item == 'spring': player.vel_y *= 1.8
                    if p.has_item == 'rocket': player.powerup_timer = 120
                    if p.has_item == 'propeller': player.powerup_timer = 60
                    if p.type == 'white': platforms.remove(p)
                    break

        for m in monsters[:]:
            for b in bullets[:]:
                if b.rect.colliderect(m.rect):
                    if b in bullets: bullets.remove(b)
                    if m in monsters: monsters.remove(m)
                    break
            if m in monsters and player.rect.colliderect(m.rect):
                if player.powerup_timer > 0:
                    monsters.remove(m)
                elif player.vel_y > 0 and player.rect.bottom < m.rect.centery:
                    monsters.remove(m)
                    player.vel_y = player.jump_power
                else: running = False

        for bh in black_holes:
            dist = math.hypot(player.rect.centerx - bh.center[0], player.rect.centery - bh.center[1])
            if dist < bh.radius + 5 and player.powerup_timer <= 0:
                running = False

        if player.rect.top > HEIGHT: running = False

        if RENDER:
            screen.fill(BACKGROUND)
            for b in bullets: b.draw(screen)
            for p in platforms: p.draw(screen)
            for m in monsters: m.draw(screen)
            for bh in black_holes: bh.draw(screen)
            player.draw(screen)
            font = pygame.font.SysFont("Arial", 18, bold=True)
            txt = font.render(f"SCORE: {int(player.score)}", True, (50, 50, 50))
            screen.blit(txt, (10, 10))
            pygame.display.flip()
            clock.tick(FPS)

    return player.score

if __name__ == "__main__":
    pygame.init()
    main_screen = pygame.display.set_mode(RESOLUTION) if RENDER else None
    pygame.display.set_caption(TITLE)
    main_clock = pygame.time.Clock()

    while True:
        final_score = run_game(main_screen, main_clock)
        if final_score is None: # User closed the window
            break
        print(f"Game Over! Score: {int(final_score)}")

    pygame.quit()
    sys.exit()
