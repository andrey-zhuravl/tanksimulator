from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from . import config


@dataclass
class Projectile:
    position: pygame.math.Vector2
    velocity: pygame.math.Vector2
    lifetime: float = config.PROJECTILE_LIFETIME

    def update(self, dt: float) -> bool:
        """Advance projectile and return False when it should be removed."""
        self.position += self.velocity * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            return False

        if (
            self.position.x < 0
            or self.position.x > config.SCREEN_WIDTH
            or self.position.y < 0
            or self.position.y > config.SCREEN_HEIGHT
        ):
            return False
        return True

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(
            surface,
            config.PROJECTILE_COLOR,
            (int(self.position.x), int(self.position.y)),
            5,
        )

    @classmethod
    def from_tank(cls, origin: pygame.math.Vector2, angle_deg: float) -> "Projectile":
        angle_rad = math.radians(angle_deg)
        direction = pygame.math.Vector2(math.cos(angle_rad), math.sin(angle_rad))
        velocity = direction * config.PROJECTILE_SPEED
        return cls(position=origin.copy(), velocity=velocity)
