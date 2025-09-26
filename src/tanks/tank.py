from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List

import pygame

from . import config
from .projectile import Projectile


@dataclass
class Tank:
    position: pygame.math.Vector2
    angle: float = 0.0
    turret_angle: float = 0.0
    color: tuple[int, int, int] = config.PLAYER_TANK_COLOR
    turret_color: tuple[int, int, int] = config.TURRET_COLOR
    is_player: bool = False
    cooldown: float = 0.0
    projectiles: List[Projectile] = field(default_factory=list)

    move_speed: float = 220.0
    rotation_speed: float = 120.0
    turret_rotation_speed: float = 160.0
    reload_time: float = 0.8

    def update(self, dt: float) -> None:
        if self.cooldown > 0:
            self.cooldown = max(0.0, self.cooldown - dt)

        alive_projectiles: List[Projectile] = []
        for projectile in self.projectiles:
            if projectile.update(dt):
                alive_projectiles.append(projectile)
        self.projectiles = alive_projectiles

    def draw(self, surface: pygame.Surface) -> None:
        body_width, body_height = config.TANK_BODY_SIZE
        rect = pygame.Rect(0, 0, body_width, body_height)
        rect.center = self.position

        rotated_body = pygame.Surface((body_width, body_height), pygame.SRCALPHA)
        pygame.draw.rect(rotated_body, self.color, rotated_body.get_rect(), border_radius=10)
        rotated_body = pygame.transform.rotate(rotated_body, -self.angle)
        surface.blit(rotated_body, rotated_body.get_rect(center=self.position))

        # Turret
        turret_surface = pygame.Surface((body_width, body_width), pygame.SRCALPHA)
        pygame.draw.circle(
            turret_surface,
            self.turret_color,
            (body_width // 2, body_width // 2),
            body_width // 2 - 6,
            width=0,
        )
        pygame.draw.line(
            turret_surface,
            self.turret_color,
            (body_width // 2, body_width // 2),
            (
                body_width // 2 + config.TANK_TURRET_LENGTH,
                body_width // 2,
            ),
            8,
        )
        rotated_turret = pygame.transform.rotate(turret_surface, -self.turret_angle)
        surface.blit(rotated_turret, rotated_turret.get_rect(center=self.position))

        for projectile in self.projectiles:
            projectile.draw(surface)

    def forward_vector(self) -> pygame.math.Vector2:
        angle_rad = math.radians(self.angle)
        return pygame.math.Vector2(math.cos(angle_rad), math.sin(angle_rad))

    def turret_tip(self) -> pygame.math.Vector2:
        angle_rad = math.radians(self.turret_angle)
        return self.position + pygame.math.Vector2(
            math.cos(angle_rad) * (config.TANK_BODY_SIZE[1] // 2 + config.TANK_TURRET_LENGTH),
            math.sin(angle_rad) * (config.TANK_BODY_SIZE[1] // 2 + config.TANK_TURRET_LENGTH),
        )

    def move_forward(self, dt: float) -> None:
        self.position += self.forward_vector() * self.move_speed * dt
        self._clamp_to_field()

    def move_backward(self, dt: float) -> None:
        self.position -= self.forward_vector() * self.move_speed * dt
        self._clamp_to_field()

    def rotate_left(self, dt: float) -> None:
        self.angle = (self.angle - self.rotation_speed * dt) % 360

    def rotate_right(self, dt: float) -> None:
        self.angle = (self.angle + self.rotation_speed * dt) % 360

    def rotate_turret_left(self, dt: float) -> None:
        self.turret_angle = (self.turret_angle - self.turret_rotation_speed * dt) % 360

    def rotate_turret_right(self, dt: float) -> None:
        self.turret_angle = (self.turret_angle + self.turret_rotation_speed * dt) % 360

    def fire(self) -> None:
        if self.cooldown > 0:
            return
        projectile = Projectile.from_tank(self.turret_tip(), self.turret_angle)
        self.projectiles.append(projectile)
        self.cooldown = self.reload_time

    def _clamp_to_field(self) -> None:
        margin = config.FIELD_MARGIN + config.TANK_BODY_SIZE[0] // 2
        self.position.x = max(margin, min(config.SCREEN_WIDTH - margin, self.position.x))
        self.position.y = max(margin, min(config.SCREEN_HEIGHT - margin, self.position.y))
