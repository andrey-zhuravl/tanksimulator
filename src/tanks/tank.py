from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, List

import pygame

from . import config
from .projectile import Projectile, ProjectileState


@dataclass
class Tank:
    position: pygame.math.Vector2
    angle: float = 0.0
    turret_angle: float = 0.0
    color: tuple[int, int, int] = config.PLAYER_TANK_COLOR
    turret_color: tuple[int, int, int] = config.TURRET_COLOR
    identifier: str | None = None
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
        _draw_tank_surface(
            surface,
            self.position,
            self.angle,
            self.turret_angle,
            self.color,
            self.turret_color,
            (projectile.to_state() for projectile in self.projectiles),
        )

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

    def to_state(self, team: str) -> "TankState":
        return TankState(
            identifier=self.identifier or "",
            team=team,
            x=float(self.position.x),
            y=float(self.position.y),
            angle=float(self.angle),
            turret_angle=float(self.turret_angle),
            color=tuple(self.color),
            turret_color=tuple(self.turret_color),
            is_player=self.is_player,
            projectiles=[projectile.to_state() for projectile in self.projectiles],
        )


@dataclass
class TankState:
    identifier: str
    team: str
    x: float
    y: float
    angle: float
    turret_angle: float
    color: tuple[int, int, int]
    turret_color: tuple[int, int, int]
    is_player: bool = False
    projectiles: List[ProjectileState] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.identifier,
            "team": self.team,
            "x": self.x,
            "y": self.y,
            "angle": self.angle,
            "turret_angle": self.turret_angle,
            "color": list(self.color),
            "turret_color": list(self.turret_color),
            "is_player": self.is_player,
            "projectiles": [p.to_dict() for p in self.projectiles],
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "TankState":
        return cls(
            identifier=str(payload["id"]),
            team=str(payload["team"]),
            x=float(payload["x"]),
            y=float(payload["y"]),
            angle=float(payload["angle"]),
            turret_angle=float(payload["turret_angle"]),
            color=tuple(payload.get("color", config.PLAYER_TANK_COLOR)),
            turret_color=tuple(payload.get("turret_color", config.TURRET_COLOR)),
            is_player=bool(payload.get("is_player", False)),
            projectiles=[ProjectileState.from_dict(p) for p in payload.get("projectiles", [])],
        )

    def draw(self, surface: pygame.Surface) -> None:
        position = pygame.math.Vector2(self.x, self.y)
        _draw_tank_surface(
            surface,
            position,
            self.angle,
            self.turret_angle,
            self.color,
            self.turret_color,
            self.projectiles,
        )


def _draw_tank_surface(
    surface: pygame.Surface,
    position: pygame.math.Vector2,
    angle: float,
    turret_angle: float,
    color: tuple[int, int, int],
    turret_color: tuple[int, int, int],
    projectiles: Iterable[ProjectileState],
) -> None:
    body_width, body_height = config.TANK_BODY_SIZE

    rotated_body = pygame.Surface((body_width, body_height), pygame.SRCALPHA)
    pygame.draw.rect(rotated_body, color, rotated_body.get_rect(), border_radius=10)
    rotated_body = pygame.transform.rotate(rotated_body, -angle)
    surface.blit(rotated_body, rotated_body.get_rect(center=position))

    turret_surface = pygame.Surface((body_width, body_width), pygame.SRCALPHA)
    pygame.draw.circle(
        turret_surface,
        turret_color,
        (body_width // 2, body_width // 2),
        body_width // 2 - 6,
        width=0,
    )
    pygame.draw.line(
        turret_surface,
        turret_color,
        (body_width // 2, body_width // 2),
        (
            body_width // 2 + config.TANK_TURRET_LENGTH,
            body_width // 2,
        ),
        8,
    )
    rotated_turret = pygame.transform.rotate(turret_surface, -turret_angle)
    surface.blit(rotated_turret, rotated_turret.get_rect(center=position))

    for projectile in projectiles:
        projectile.draw(surface)
