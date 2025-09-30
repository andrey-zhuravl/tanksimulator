"""Definitions for individual bodies in the simulation."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List

import pygame


@dataclass
class GravityPoint:
    """A simple body affected by gravity."""

    position: pygame.Vector3
    velocity: pygame.Vector3
    mass: float
    color: tuple[int, int, int]
    group_index: int
    trail: List[pygame.Vector3] = field(default_factory=list)

    def limit_speed(self, max_speed: float) -> None:
        max_speed_sq = max_speed * max_speed
        velocity_sq = self.velocity.length_squared()
        if velocity_sq > max_speed_sq and velocity_sq > 0:
            scale = math.sqrt(max_speed_sq / velocity_sq)
            self.velocity *= scale
