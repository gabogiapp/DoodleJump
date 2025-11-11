"""
Game constants and configuration settings.
All visual colors, sizes, and physics parameters are defined here.
"""

# Screen dimensions
WIDTH = 400
HEIGHT = 600
FPS = 60

# Colors - cohesive pastel/retro palette
COLOR_BACKGROUND_START = (173, 216, 230)  # Light blue
COLOR_BACKGROUND_END = (255, 255, 255)    # White
COLOR_PLATFORM = (76, 175, 80)            # Green
COLOR_PLATFORM_BREAKABLE = (255, 152, 0)  # Orange
COLOR_PLATFORM_SPRING = (33, 150, 243)    # Blue
COLOR_PLAYER = (244, 67, 54)              # Red
COLOR_TEXT = (33, 33, 33)                 # Dark gray
COLOR_TEXT_LIGHT = (158, 158, 158)        # Light gray
COLOR_PARTICLE = (255, 235, 59)           # Yellow for particles

# Player settings
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 40
PLAYER_HORIZONTAL_SPEED = 200  # pixels per second
PLAYER_JUMP_VELOCITY = -450    # negative = upward
PLAYER_SPRING_BOOST = -650     # super jump velocity

# Physics
GRAVITY = 800  # pixels per second squared

# Platform settings
PLATFORM_WIDTH = 80
PLATFORM_HEIGHT = 16
PLATFORM_SPACING = 120  # Vertical spacing between platforms
PLATFORM_BORDER_RADIUS = 8  # Rounded corners

# Platform generation for completability
# Maximum horizontal distance player can jump (calculated from physics)
# Jump time = 2 * (jump_velocity / gravity) = 2 * (450 / 800) ≈ 1.125s
# Max horizontal distance = horizontal_speed * jump_time = 200 * 1.125 ≈ 225px
# Using conservative value accounting for player/platform widths and collision margins
MAX_JUMP_HORIZONTAL_DISTANCE = 200  # Maximum safe horizontal distance between platform centers
PLATFORM_MIN_OFFSET = 30  # Minimum horizontal offset from previous platform (for variety)
PLATFORM_MAX_OFFSET = 140  # Max center-to-center offset ensuring reachability (conservative)

# Platform probabilities (should sum to <= 1.0)
PLATFORM_NORMAL_CHANCE = 0.70
PLATFORM_BREAKABLE_CHANCE = 0.20
PLATFORM_SPRING_CHANCE = 0.10

# Camera settings
CAMERA_DEAD_ZONE_TOP = HEIGHT * 0.3  # Start scrolling when player reaches 30% from top (180px)
# This keeps player in lower 70% of screen, allowing them to see platforms above

# Game settings
INITIAL_PLATFORM_COUNT = 15  # Platforms generated at start
PLATFORM_BUFFER_ZONE = 100   # Generate platforms this far above screen

# Particle effects
PARTICLE_COUNT = 8
PARTICLE_LIFETIME = 0.3  # seconds
PARTICLE_SPEED = 50      # pixels per second

# Font settings
FONT_SIZE_LARGE = 48
FONT_SIZE_MEDIUM = 24
FONT_SIZE_SMALL = 18
