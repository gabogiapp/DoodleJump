# Doodle Jump - Python/Pygame Version

A clean, well-structured Doodle Jump-style game built with Python and Pygame.

## Features

- **Smooth Physics**: Frame-independent movement using delta time
- **Scrolling Camera**: Dynamic camera that follows the player upward
- **Platform Types**: 
  - Normal platforms (green)
  - Breakable platforms (orange) - break when jumped on
  - Spring platforms (blue) - provide super jump boost
- **Visual Effects**: Particle effects when landing on platforms
- **Score System**: Score increases as you climb higher
- **Game Over & Restart**: Press R to restart after game over

## Requirements

- Python 3.7+
- Pygame 2.5.0+

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Game

```bash
python main.py
```

## Controls

- **Arrow Keys** or **A/D**: Move left/right
- **R**: Restart game (when game over)
- **ESC**: Quit game

## Game Mechanics

- The player automatically jumps when landing on platforms
- The camera scrolls upward as you climb higher
- Platforms are randomly generated above the screen
- Falling below the bottom of the screen results in game over
- Score increases based on how high you climb

## Code Structure

- `main.py`: Entry point
- `game.py`: Main game class and game loop
- `player.py`: Player character class
- `platform.py`: Platform class with collision detection
- `assets.py`: Asset manager for loading and sizing images
- `constants.py`: All game constants and configuration

## Asset Sizing

All assets are automatically resized to consistent dimensions:
- Player: 40x40 pixels
- Platforms: 80x16 pixels
- Spring: 20x20 pixels

The asset manager ensures all images are properly scaled and cached for performance.

