"""Configuration constants for the metronome circle application."""

from typing import Tuple

WINDOW_SIZE: Tuple[int, int] = (640, 640)
BACKGROUND_COLOR: Tuple[int, int, int] = (20, 20, 30)
CIRCLE_COLOR: Tuple[int, int, int] = (240, 240, 240)
ACCENT_COLOR: Tuple[int, int, int] = (220, 160, 60)
CURRENT_STEP_COLOR: Tuple[int, int, int] = (185, 55, 120)
DEFAULT_NODE_COLOR: Tuple[int, int, int] = (20, 220, 230)
POLYGON_COLOR: Tuple[int, int, int] = (200, 50, 50)
TEXT_COLOR: Tuple[int, int, int] = (210, 210, 220)

NUM_STEPS: int = 17
NODE_RADIUS: int = 19
OUTLINE_WIDTH: int = 5
SEQUENCE_DURATION_SECONDS: float = 2.5
