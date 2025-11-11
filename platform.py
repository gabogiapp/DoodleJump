"""
Platform class - handles platform rendering and collision detection.
"""

import pygame
from constants import (
    PLATFORM_WIDTH, PLATFORM_HEIGHT, PLATFORM_BORDER_RADIUS,
    COLOR_PLATFORM, COLOR_PLATFORM_BREAKABLE, COLOR_PLATFORM_SPRING,
    WIDTH
)


class Platform:
    """A platform that the player can jump on."""
    
    def __init__(self, x, y, assets, kind="normal"):
        """
        Initialize a platform.
        
        Args:
            x: X position (left edge)
            y: Y position (top edge)
            assets: AssetManager instance
            kind: Platform type ("normal", "breakable", "spring")
        """
        self.assets = assets
        self.x = x
        self.y = y
        self.kind = kind
        self.width = PLATFORM_WIDTH
        self.height = PLATFORM_HEIGHT
        self.broken = False
        
        # Load platform image
        self.image = self._load_image()
        
        # Spring sprite (for spring platforms)
        self.spring_image = None
        if self.kind == "spring":
            self.spring_image = assets.load_spring()
        
        # Bounding rectangle for collision
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def _load_image(self):
        """Load the appropriate platform image based on type."""
        if self.kind == "breakable":
            return self.assets.load_platform_breakable()
        elif self.kind == "normal" or self.kind == "spring":
            return self.assets.load_platform_normal()
        return None
    
    def move(self, dy):
        """
        Move platform vertically (used for scrolling).
        
        Args:
            dy: Vertical offset in pixels
        """
        self.y += dy
        self.rect.y = self.y
    
    def relocate(self, x, y, kind=None):
        """
        Relocate platform to new position and optionally change type.
        
        Args:
            x: New x position
            y: New y position
            kind: New platform type (optional)
        """
        self.x = max(0, min(x, WIDTH - self.width))
        self.y = y
        if kind:
            self.kind = kind
            self.image = self._load_image()
            self.spring_image = self.assets.load_spring() if self.kind == "spring" else None
            self.broken = False
        self.rect.x = self.x
        self.rect.y = self.y
    
    def collides(self, player):
        """
        Check if player collides with this platform.
        Only checks collision when player is falling.
        
        Args:
            player: Player instance
        
        Returns:
            True if collision detected, False otherwise
        """
        if self.broken:
            return False
        
        # Only collide when player is moving downward
        # and player's bottom is within platform's vertical range
        player_bottom = player.bottom
        platform_top = self.y
        platform_bottom = self.y + self.height
        
        if player_bottom < platform_top or player_bottom > platform_bottom:
            return False
        
        # Check horizontal overlap
        return player.right > self.x and player.left < self.x + self.width
    
    def on_land(self, player):
        """
        Handle player landing on platform.
        
        Args:
            player: Player instance
        
        Returns:
            True if player should jump, False if platform breaks
        """
        if self.kind == "breakable":
            if not self.broken:
                self.break_platform()
            return False
        
        if self.kind == "spring":
            player.super_jump()
        else:
            player.jump()
        
        return True
    
    def break_platform(self):
        """Break the platform (for breakable platforms)."""
        self.broken = True
    
    def draw(self, surface, camera_y=0):
        """
        Draw the platform on the surface.
        
        Args:
            surface: pygame.Surface to draw on
            camera_y: Camera offset (for scrolling effects)
        """
        if self.broken:
            return
        
        draw_y = self.y - camera_y
        
        # Don't draw if outside visible area
        if draw_y < -self.height or draw_y > surface.get_height() + self.height:
            return
        
        # Determine platform color based on type
        if self.image:
            # Draw image
            surface.blit(self.image, (self.x, draw_y))
        else:
            # Draw default rounded rectangle
            color = COLOR_PLATFORM
            if self.kind == "breakable":
                color = COLOR_PLATFORM_BREAKABLE
            elif self.kind == "spring":
                color = COLOR_PLATFORM_SPRING
            
            # Draw rounded rectangle
            rect = pygame.Rect(self.x, draw_y, self.width, self.height)
            pygame.draw.rect(surface, color, rect, border_radius=PLATFORM_BORDER_RADIUS)
            # Add a subtle highlight using a lighter shade
            highlight_color = tuple(min(255, c + 40) for c in color)
            highlight_rect = pygame.Rect(self.x + 2, draw_y + 2, self.width - 4, 4)
            pygame.draw.rect(surface, highlight_color, highlight_rect, border_radius=2)
        
        # Draw spring on spring platforms
        if self.kind == "spring" and self.spring_image:
            spring_x = self.x + (self.width - self.spring_image.get_width()) // 2
            spring_y = draw_y - self.spring_image.get_height() + 4
            surface.blit(self.spring_image, (spring_x, spring_y))
