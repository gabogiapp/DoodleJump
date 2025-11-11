"""
Player class - handles the doodler character movement and physics.
"""

import pygame
from constants import (
    WIDTH, HEIGHT, PLAYER_WIDTH, PLAYER_HEIGHT,
    PLAYER_HORIZONTAL_SPEED, PLAYER_JUMP_VELOCITY, PLAYER_SPRING_BOOST,
    GRAVITY, COLOR_PLAYER
)


class Player:
    """The player character (doodler) that jumps on platforms."""
    
    def __init__(self, x, y, assets):
        """
        Initialize the player.
        
        Args:
            x: Initial x position
            y: Initial y position
            assets: AssetManager instance
        """
        self.assets = assets
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        
        # Position (center of player)
        self.x = x
        self.y = y
        
        # Velocity (pixels per second)
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        
        # Direction: -1 (left), 0 (none), 1 (right)
        self.direction = 0
        
        # Load player image or use default shape
        self.image = assets.load_player()
        self.use_image = self.image is not None
        
        # Bounding box for collision detection
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self._update_rect()
    
    def set_direction(self, direction):
        """
        Set horizontal movement direction.
        
        Args:
            direction: -1 (left), 0 (none), 1 (right)
        """
        self.direction = direction
    
    def jump(self):
        """Make the player jump with normal velocity."""
        self.velocity_y = PLAYER_JUMP_VELOCITY
    
    def super_jump(self):
        """Make the player jump with spring boost velocity."""
        self.velocity_y = PLAYER_SPRING_BOOST
    
    def update(self, dt):
        """
        Update player position and physics.
        
        Args:
            dt: Delta time in seconds since last update
        """
        # Apply horizontal movement
        if self.direction != 0:
            self.velocity_x = self.direction * PLAYER_HORIZONTAL_SPEED
        else:
            self.velocity_x = 0
        
        # Apply gravity
        self.velocity_y += GRAVITY * dt
        
        # Update position
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        
        # Wrap around screen horizontally
        if self.x < -self.width / 2:
            self.x = WIDTH + self.width / 2
        elif self.x > WIDTH + self.width / 2:
            self.x = -self.width / 2
        
        # Update bounding box
        self._update_rect()
    
    def _update_rect(self):
        """Update the bounding rectangle for collision detection."""
        self.rect.centerx = self.x
        self.rect.centery = self.y
        self.rect.width = self.width
        self.rect.height = self.height
    
    def draw(self, surface, camera_y=0):
        """
        Draw the player on the surface.
        
        Args:
            surface: pygame.Surface to draw on
            camera_y: Camera offset (for scrolling effects)
        """
        draw_y = self.y - camera_y
        
        # Draw player even if slightly outside screen bounds (for smooth transitions)
        # Only skip drawing if way off screen
        if draw_y < -self.height * 2 or draw_y > HEIGHT + self.height * 2:
            return
        
        if self.use_image and self.image:
            # Draw image centered on player position
            image_rect = self.image.get_rect(center=(self.x, draw_y))
            surface.blit(self.image, image_rect)
        else:
            # Draw default circular player
            pygame.draw.circle(
                surface,
                COLOR_PLAYER,
                (int(self.x), int(draw_y)),
                self.width // 2
            )
            # Add a simple face
            eye_offset = self.width // 6
            pygame.draw.circle(
                surface,
                (255, 255, 255),
                (int(self.x - eye_offset), int(draw_y - eye_offset)),
                4
            )
            pygame.draw.circle(
                surface,
                (255, 255, 255),
                (int(self.x + eye_offset), int(draw_y - eye_offset)),
                4
            )
    
    @property
    def left(self):
        """Left edge of player."""
        return self.rect.left
    
    @property
    def right(self):
        """Right edge of player."""
        return self.rect.right
    
    @property
    def top(self):
        """Top edge of player."""
        return self.rect.top
    
    @property
    def bottom(self):
        """Bottom edge of player."""
        return self.rect.bottom
