"""
Main game class - handles game loop, rendering, and game state.
"""

import random
import pygame

from constants import (
    WIDTH, HEIGHT, FPS, COLOR_BACKGROUND_START, COLOR_BACKGROUND_END,
    COLOR_TEXT, COLOR_TEXT_LIGHT, COLOR_PARTICLE,
    PLATFORM_SPACING, PLATFORM_BUFFER_ZONE,
    INITIAL_PLATFORM_COUNT,
    PLATFORM_NORMAL_CHANCE, PLATFORM_BREAKABLE_CHANCE, PLATFORM_SPRING_CHANCE,
    CAMERA_DEAD_ZONE_TOP,
    PARTICLE_COUNT, PARTICLE_LIFETIME, PARTICLE_SPEED,
    FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL,
    MAX_JUMP_HORIZONTAL_DISTANCE, PLATFORM_MIN_OFFSET, PLATFORM_MAX_OFFSET,
    PLATFORM_WIDTH
)
from player import Player
from platform import Platform
from assets import AssetManager


class Particle:
    """Simple particle for landing effects."""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.velocity_x = random.uniform(-PARTICLE_SPEED, PARTICLE_SPEED)
        self.velocity_y = random.uniform(-PARTICLE_SPEED, PARTICLE_SPEED)
        self.lifetime = PARTICLE_LIFETIME
        self.age = 0.0
    
    def update(self, dt):
        """Update particle position and lifetime."""
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        self.age += dt
        return self.age < self.lifetime
    
    def draw(self, surface, camera_y=0):
        """Draw the particle with alpha transparency."""
        draw_y = self.y - camera_y
        alpha = int(255 * (1 - self.age / self.lifetime))
        size = max(1, int(3 * (1 - self.age / self.lifetime)))
        
        if size > 0 and alpha > 0:
            # Create a temporary surface with per-pixel alpha for the particle
            particle_surface = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
            color_with_alpha = (*COLOR_PARTICLE, alpha)
            pygame.draw.circle(particle_surface, color_with_alpha, (size + 1, size + 1), size)
            surface.blit(particle_surface, (int(self.x) - size - 1, int(draw_y) - size - 1))


class Game:
    """Main game class managing the game loop and state."""
    
    def __init__(self):
        """Initialize the game."""
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Doodle Jump")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, FONT_SIZE_LARGE)
        self.font_medium = pygame.font.Font(None, FONT_SIZE_MEDIUM)
        self.font_small = pygame.font.Font(None, FONT_SIZE_SMALL)
        
        # Asset management
        self.assets = AssetManager()
        
        # Game state
        self.running = True
        self.game_over = False
        self.score = 0
        
        # Camera offset (for scrolling) - represents how far we've scrolled
        # camera_y increases as player climbs higher (world scrolls down)
        # Start camera at 0 - no scrolling initially
        self.camera_y = 0
        
        # Player starts in world coordinates
        # We want player to start visible on screen, near the bottom
        # With camera_y = 0, screen_y = world_y
        # So set world_y to a visible screen position (near bottom)
        initial_world_y = HEIGHT - 100  # Start player at y=500 (visible, near bottom)
        self.highest_world_y = initial_world_y  # Track highest world y position
        
        self.player = Player(WIDTH // 2, initial_world_y, self.assets)
        self.platforms = []
        self.particles = []
        
        # Input state
        self.keys_pressed = set()
        
        # Cached background surface for performance
        self.background_surface = self._create_background()
        
        # Initialize platforms
        self._generate_initial_platforms()
        
        # Give player initial jump - they'll jump up and camera will follow
        self.player.jump()

    def _generate_initial_platforms(self):
        """Generate initial set of platforms in world coordinates.
        
        Ensures platforms are always reachable by limiting horizontal distance.
        """
        # Start platform should be at player's starting position or slightly below
        # Player starts at world_y = HEIGHT - 100
        # Platform should be at similar height so player can land on it
        player_start_y = HEIGHT - 100
        start_y = player_start_y + 20  # Platform slightly below player (they'll land on it)
        start_x = WIDTH // 2 - PLATFORM_WIDTH // 2
        start_platform = Platform(
            start_x,
            start_y,
            self.assets,
            kind="normal"
        )
        self.platforms.append(start_platform)
        
        # Track previous platform position for reachability
        prev_x = start_x + PLATFORM_WIDTH // 2  # Center of previous platform
        current_y = start_y - PLATFORM_SPACING
        
        # Generate platforms going upward, ensuring each is reachable
        for i in range(INITIAL_PLATFORM_COUNT):
            # Calculate reachable x position relative to previous platform
            # Choose random direction (left or right)
            direction = random.choice([-1, 1])
            
            # Random offset between MIN and MAX in chosen direction
            # This ensures platforms are always reachable but have variety
            offset_magnitude = random.randint(PLATFORM_MIN_OFFSET, PLATFORM_MAX_OFFSET)
            offset = direction * offset_magnitude
            
            # Calculate new platform center
            new_center_x = prev_x + offset
            
            # Clamp to screen bounds with margins
            margin = 10
            new_center_x = max(PLATFORM_WIDTH // 2 + margin, 
                              min(new_center_x, WIDTH - PLATFORM_WIDTH // 2 - margin))
            
            # Platform x is left edge
            x = new_center_x - PLATFORM_WIDTH // 2
            
            # Random platform type (but ensure first few are normal for easier start)
            if i < 3:
                kind = "normal"
        else:
            kind = self._random_platform_kind()
            
            platform = Platform(x, current_y, self.assets, kind=kind)
            self.platforms.append(platform)
            
            # Update for next iteration
            prev_x = new_center_x
            current_y -= PLATFORM_SPACING + random.randint(-15, 15)
    
    def _random_platform_kind(self):
        """Generate a random platform type based on probabilities."""
        rand = random.random()
        if rand < PLATFORM_SPRING_CHANCE:
            return "spring"
        elif rand < PLATFORM_SPRING_CHANCE + PLATFORM_BREAKABLE_CHANCE:
            return "breakable"
        else:
            return "normal"
    
    def _handle_input(self):
        """Handle keyboard input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r and self.game_over:
                    self._restart()
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self.player.set_direction(-1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.player.set_direction(1)
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                    # Check if opposite key is still pressed
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                        self.player.set_direction(-1)
                    elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                        self.player.set_direction(1)
                    else:
                        self.player.set_direction(0)
        
        # Handle held keys
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            if not (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
                self.player.set_direction(-1)
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.set_direction(1)
        else:
            self.player.set_direction(0)
    
    def _update(self, dt):
        """
        Update game logic.
        
        Args:
            dt: Delta time in seconds
        """
        if self.game_over:
            return
        
        # Update player (in world coordinates)
        self.player.update(dt)
        
        # Update particles
        self.particles = [p for p in self.particles if p.update(dt)]
        
        # Handle collisions
        self._handle_collisions()
        
        # Update camera and scrolling (also updates score)
        self._update_camera()
        
        # Update highest point reached (world coordinates)
        if self.player.y < self.highest_world_y:
            self.highest_world_y = self.player.y
        
        # Check game over condition - player falls below screen bottom in screen coordinates
        player_screen_y = self.player.y - self.camera_y
        if player_screen_y > HEIGHT + 50:
            self._end_game()
        
        # Generate new platforms as needed
        self._generate_platforms()

    def _handle_collisions(self):
        """Handle collisions between player and platforms."""
        # Only check collisions when player is falling
        if self.player.velocity_y <= 0:
            return
        
        for platform in self.platforms:
            if platform.collides(self.player):
                if platform.on_land(self.player):
                    # Create landing particles
                    self._create_landing_particles(platform.x + platform.width // 2, platform.y)
                    break

    def _create_landing_particles(self, x, y):
        """Create particle effect at landing position (world coordinates)."""
        for _ in range(PARTICLE_COUNT):
            self.particles.append(Particle(x, y))
    
    def _update_camera(self):
        """Update camera position for scrolling effect.
        
        In Doodle Jump style: as player climbs up (world_y decreases), 
        the camera follows by increasing camera_y, which makes the world
        scroll down on screen. The player stays visible in the upper portion
        of the screen while the world moves beneath them.
        """
        # Calculate player's screen position
        # Formula: screen_y = world_y - camera_y
        player_screen_y = self.player.y - self.camera_y
        
        # CRITICAL: Ensure player is always visible on screen
        # If player goes above the dead zone OR above screen top, scroll immediately
        if player_screen_y < CAMERA_DEAD_ZONE_TOP or player_screen_y < 0:
            # Calculate target camera position to keep player at dead zone
            # We want: player_screen_y = CAMERA_DEAD_ZONE_TOP (after scrolling)
            # So: CAMERA_DEAD_ZONE_TOP = player.y - new_camera_y
            # Therefore: new_camera_y = player.y - CAMERA_DEAD_ZONE_TOP
            target_camera_y = self.player.y - CAMERA_DEAD_ZONE_TOP
            
            # Only scroll upward (camera_y can only increase, never decrease)
            # This ensures we only scroll when player is climbing, not falling
            old_camera_y = self.camera_y
            
            # If player is above screen, immediately bring into view
            # Otherwise, scroll to keep player at dead zone
            if player_screen_y < 0 or target_camera_y > self.camera_y:
                self.camera_y = target_camera_y
                scroll_distance = self.camera_y - old_camera_y
            else:
                scroll_distance = 0
            
            # Update score based on distance climbed
            if scroll_distance > 0:
                self.score += max(1, int(scroll_distance / 3))
    
    def _generate_platforms(self):
        """Generate new platforms above the screen as needed.
        
        Ensures platforms are always reachable by tracking the last platform
        and limiting horizontal distance between consecutive platforms.
        """
        if not self.platforms:
            return
        
        # Find the highest platform (lowest y value in world coordinates)
        highest_platform = min(self.platforms, key=lambda p: p.y)
        
        # Calculate what world y position is currently at the top of the screen
        top_of_screen_world_y = self.camera_y
        
        # Use the highest platform as reference for generating the next one
        # This ensures we build upward from the highest existing platform
        last_platform = highest_platform
        last_center_x = last_platform.x + last_platform.width // 2
        
        # Generate platforms above the current view
        while highest_platform.y > top_of_screen_world_y - PLATFORM_BUFFER_ZONE:
            # Calculate new y position (above the last platform)
            new_y = last_platform.y - PLATFORM_SPACING - random.randint(-15, 15)
            
            # Calculate reachable x position relative to last platform
            # Offset must be within jump range to ensure reachability
            # Choose random direction (left or right)
            direction = random.choice([-1, 1])
            
            # Random offset between MIN and MAX in chosen direction
            # This ensures platforms are always reachable but have variety
            offset_magnitude = random.randint(PLATFORM_MIN_OFFSET, PLATFORM_MAX_OFFSET)
            offset = direction * offset_magnitude
            
            # Ensure offset stays within max jump distance (safety check)
            offset = max(-PLATFORM_MAX_OFFSET, min(PLATFORM_MAX_OFFSET, offset))
            
            # Calculate new platform center
            new_center_x = last_center_x + offset
            
            # Clamp to screen bounds with margins
            margin = 10
            new_center_x = max(PLATFORM_WIDTH // 2 + margin, 
                              min(new_center_x, WIDTH - PLATFORM_WIDTH // 2 - margin))
            
            # Platform x is left edge
            x = new_center_x - PLATFORM_WIDTH // 2
            
            # Random platform type
            kind = self._random_platform_kind()
            
            platform = Platform(x, new_y, self.assets, kind=kind)
            self.platforms.append(platform)
            
            # Update references for next iteration
            last_platform = platform
            last_center_x = new_center_x
            highest_platform = platform
        
        # Remove platforms that are too far below the screen
        bottom_of_screen_world_y = self.camera_y + HEIGHT
        self.platforms = [p for p in self.platforms if p.y < bottom_of_screen_world_y + 200]
    
    def _create_background(self):
        """Create a cached background surface with gradient."""
        surface = pygame.Surface((WIDTH, HEIGHT))
        # Draw gradient from light blue to white
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            r = int(COLOR_BACKGROUND_START[0] * (1 - ratio) + COLOR_BACKGROUND_END[0] * ratio)
            g = int(COLOR_BACKGROUND_START[1] * (1 - ratio) + COLOR_BACKGROUND_END[1] * ratio)
            b = int(COLOR_BACKGROUND_START[2] * (1 - ratio) + COLOR_BACKGROUND_END[2] * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))
        return surface
    
    def _draw_background(self):
        """Draw the cached background."""
        self.screen.blit(self.background_surface, (0, 0))
    
    def _draw(self):
        """Draw everything on the screen."""
        # Clear screen with background
        self._draw_background()
        
        # Draw platforms
        for platform in self.platforms:
            platform.draw(self.screen, self.camera_y)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen, self.camera_y)
        
        # Draw player (always draw - player draw method handles visibility)
        self.player.draw(self.screen, self.camera_y)
        
        # Draw UI
        self._draw_ui()
        
        # Draw game over screen
        if self.game_over:
            self._draw_game_over()
        
        pygame.display.flip()
    
    def _draw_ui(self):
        """Draw user interface (score, etc.)."""
        # Draw score
        score_text = self.font_medium.render(f"Score: {self.score}", True, COLOR_TEXT)
        self.screen.blit(score_text, (10, 10))
        
        # Draw height (based on world coordinates)
        height = max(0, int((HEIGHT - 100 - self.highest_world_y) / 10))
        height_text = self.font_small.render(
            f"Height: {height}",
            True,
            COLOR_TEXT_LIGHT
        )
        self.screen.blit(height_text, (10, 40))
    
    def _draw_game_over(self):
        """Draw game over screen."""
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Game over text
        game_over_text = self.font_large.render("Game Over", True, (255, 255, 255))
        text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
        self.screen.blit(game_over_text, text_rect)
        
        # Final score
        score_text = self.font_medium.render(f"Final Score: {self.score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(score_text, score_rect)
        
        # Restart instruction
        restart_text = self.font_small.render("Press R to restart", True, (200, 200, 200))
        restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
        self.screen.blit(restart_text, restart_rect)

    def _end_game(self):
        """End the game."""
        self.game_over = True
    
    def _restart(self):
        """Restart the game."""
        self.game_over = False
        self.score = 0
        self.highest_world_y = HEIGHT - 100
        self.camera_y = 0
        self.particles = []
        
        # Reset player to initial world position
        initial_world_y = HEIGHT - 100
        self.player = Player(WIDTH // 2, initial_world_y, self.assets)
        self.player.jump()
        
        # Regenerate platforms
        self.platforms = []
        self._generate_initial_platforms()
        
        # Reset background cache (in case we want dynamic backgrounds later)
        self.background_surface = self._create_background()
    
    def run(self):
        """Run the main game loop."""
        while self.running:
            # Calculate delta time
            dt = self.clock.tick(FPS) / 1000.0  # Convert to seconds
            
            # Handle input
            self._handle_input()
            
            # Update game logic
            self._update(dt)
            
            # Draw everything
            self._draw()
        
        pygame.quit()
