"""
Asset manager for loading and scaling images consistently.
Ensures all assets are properly sized and cached.
"""

import os
import pygame

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class AssetManager:
    """Manages loading and caching of game assets with consistent sizing."""
    
    def __init__(self):
        self.cache = {}
        self._default_sizes = {
            "player": (40, 40),
            "platform": (80, 16),
            "spring": (20, 20),
            "background": None  # Use original size for background
        }
    
    def load_image(self, filename, size=None, use_cache=True):
        """
        Load an image file, optionally resize it, and cache it.
        
        Args:
            filename: Name of the image file
            size: Tuple (width, height) to resize to, or None for original size
            use_cache: Whether to use cached version if available
        
        Returns:
            pygame.Surface or None if file not found
        """
        cache_key = f"{filename}_{size}" if size else filename
        
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        path = os.path.join(BASE_DIR, filename)
        
        if not os.path.exists(path):
            return None
        
        try:
            image = pygame.image.load(path).convert_alpha()
            if size:
                image = pygame.transform.smoothscale(image, size)
            if use_cache:
                self.cache[cache_key] = image
            return image
        except pygame.error as e:
            print(f"Error loading image {filename}: {e}")
            return None
    
    def load_player(self):
        """Load player image with consistent sizing."""
        return self.load_image("DoodleJumper.jpg", self._default_sizes["player"])
    
    def load_platform_normal(self):
        """Load normal platform image with consistent sizing."""
        return self.load_image("JumpPad.png", self._default_sizes["platform"])
    
    def load_platform_breakable(self):
        """Load breakable platform image with consistent sizing."""
        return self.load_image("BreakablePad.png", self._default_sizes["platform"])
    
    def load_spring(self):
        """Load spring image with consistent sizing."""
        return self.load_image("Spring.png", self._default_sizes["spring"])
    
    def load_background(self):
        """Load background tile (used for patterns, not full background)."""
        return self.load_image("BackgroundTile.jpg", size=None)
