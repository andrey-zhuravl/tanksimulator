"""Configuration constants for the multi-panel metronome application."""

from __future__ import annotations

from typing import Tuple


# Layout ---------------------------------------------------------------------

GRID_ROWS: int = 3
GRID_COLS: int = 3
WINDOW_MARGIN: int = 24
GRID_GAP: int = 16
PANEL_WIDTH: int = 320
PANEL_HEIGHT: int = 320

WINDOW_SIZE: Tuple[int, int] = (
    WINDOW_MARGIN * 2 + GRID_COLS * PANEL_WIDTH + (GRID_COLS - 1) * GRID_GAP,
    WINDOW_MARGIN * 2 + GRID_ROWS * PANEL_HEIGHT + (GRID_ROWS - 1) * GRID_GAP,
)


# Colours --------------------------------------------------------------------

BACKGROUND_COLOR: Tuple[int, int, int] = (18, 20, 28)
PANEL_BACKGROUND: Tuple[int, int, int] = (32, 34, 48)
PANEL_BACKGROUND_DISABLED: Tuple[int, int, int] = (26, 28, 38)
PANEL_BORDER_COLOR: Tuple[int, int, int] = (70, 72, 100)
PANEL_BORDER_ACTIVE: Tuple[int, int, int] = (215, 140, 70)
CONTROL_SURFACE_COLOR: Tuple[int, int, int] = (42, 44, 60)
CIRCLE_COLOR: Tuple[int, int, int] = (240, 240, 240)
ACCENT_COLOR: Tuple[int, int, int] = (220, 160, 60)
CURRENT_STEP_COLOR: Tuple[int, int, int] = (185, 55, 120)
DEFAULT_NODE_COLOR: Tuple[int, int, int] = (20, 220, 230)
POLYGON_COLOR: Tuple[int, int, int] = (200, 50, 50)
TEXT_COLOR: Tuple[int, int, int] = (210, 210, 220)
SUBTLE_TEXT_COLOR: Tuple[int, int, int] = (150, 150, 170)
BUTTON_COLOR: Tuple[int, int, int] = (58, 60, 80)
BUTTON_HOVER_COLOR: Tuple[int, int, int] = (85, 88, 112)


# Timing ---------------------------------------------------------------------

SEQUENCE_DURATION_SECONDS: float = 2.5


# Steps and audio ------------------------------------------------------------

DEFAULT_NUM_STEPS: int = 16
MIN_STEPS: int = 3
MAX_STEPS: int = 32

DEFAULT_FIRST_FREQUENCY: int = 960
DEFAULT_OTHER_FREQUENCY: int = 720
MIN_FREQUENCY: int = 120
MAX_FREQUENCY: int = 2200
FREQUENCY_STEP: int = 20


# Drawing --------------------------------------------------------------------

NODE_RADIUS: int = 11
OUTLINE_WIDTH: int = 4
