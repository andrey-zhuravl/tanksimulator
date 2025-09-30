"""Sound generation utilities for the metronome circle."""

from __future__ import annotations

import math
from array import array

import pygame


def create_click_sound(
    *,
    frequency: int = 880,
    duration_ms: int = 70,
    volume: float = 0.6,
    sample_rate: int = 44100,
) -> pygame.mixer.Sound:
    """Create a simple click sound using a decaying sine wave."""

    total_samples = int(sample_rate * duration_ms / 1000)
    amplitude = int(32767 * volume)
    samples = array("h")

    for sample_index in range(total_samples):
        t = sample_index / sample_rate
        envelope = 1.0 - (sample_index / total_samples)
        sample_value = int(amplitude * envelope * math.sin(2 * math.pi * frequency * t))
        samples.append(sample_value)

    return pygame.mixer.Sound(buffer=samples.tobytes())
