from __future__ import annotations

import math
import random
from typing import Iterable, List

import pygame

from . import config
from .tank import Tank


class TankGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Tank Simulator")
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 24)

        self.player_tanks: List[Tank] = []
        self.enemy_tanks: List[Tank] = []
        self._create_teams()

        self.running = True

    def _create_teams(self) -> None:
        spacing = (config.SCREEN_WIDTH - 2 * config.FIELD_MARGIN) / 6
        y_player = config.SCREEN_HEIGHT * 0.75
        y_enemy = config.SCREEN_HEIGHT * 0.25

        for i in range(5):
            x = config.FIELD_MARGIN + spacing * (i + 1)
            player_tank = Tank(
                position=pygame.math.Vector2(x, y_player),
                angle=270,
                turret_angle=270,
                color=config.PLAYER_TANK_COLOR,
                is_player=(i == 0),
            )
            self.player_tanks.append(player_tank)

            enemy_tank = Tank(
                position=pygame.math.Vector2(x, y_enemy),
                angle=90,
                turret_angle=90,
                color=config.ENEMY_TANK_COLOR,
                turret_color=config.ENEMY_TANK_COLOR,
            )
            self.enemy_tanks.append(enemy_tank)

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def _update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        player = self.player_tanks[0]

        if keys[pygame.K_w]:
            player.move_forward(dt)
        if keys[pygame.K_s]:
            player.move_backward(dt)
        if keys[pygame.K_a]:
            player.rotate_left(dt)
        if keys[pygame.K_d]:
            player.rotate_right(dt)
        if keys[pygame.K_q]:
            player.rotate_turret_left(dt)
        if keys[pygame.K_e]:
            player.rotate_turret_right(dt)
        if keys[pygame.K_SPACE]:
            player.fire()

        for tank in self.player_tanks + self.enemy_tanks:
            tank.update(dt)

        self._update_enemy_ai(dt)

    def _update_enemy_ai(self, dt: float) -> None:
        player_position = self.player_tanks[0].position
        for tank in self.enemy_tanks:
            to_player = player_position - tank.position
            if to_player.length() > 1:
                desired_angle = math.degrees(math.atan2(to_player.y, to_player.x))
                angle_diff = (desired_angle - tank.turret_angle + 540) % 360 - 180
                rotation = max(-tank.turret_rotation_speed * dt, min(tank.turret_rotation_speed * dt, angle_diff))
                tank.turret_angle = (tank.turret_angle + rotation) % 360

            tank.cooldown = max(0.0, tank.cooldown - dt)
            if tank.cooldown <= 0 and random.random() < 0.02:
                tank.fire()

    def _draw(self) -> None:
        self.screen.fill(config.BACKGROUND_COLOR)
        self._draw_field()

        for tank in self.player_tanks + self.enemy_tanks:
            tank.draw(self.screen)

        self._draw_hud()
        pygame.display.flip()

    def _draw_field(self) -> None:
        rect = pygame.Rect(
            config.FIELD_MARGIN,
            config.FIELD_MARGIN,
            config.SCREEN_WIDTH - 2 * config.FIELD_MARGIN,
            config.SCREEN_HEIGHT - 2 * config.FIELD_MARGIN,
        )
        pygame.draw.rect(self.screen, (60, 60, 60), rect, width=4, border_radius=12)

    def _draw_hud(self) -> None:
        message = "WASD - движение, Q/E - башня, SPACE - огонь"
        text_surface = self.font.render(message, True, (220, 220, 220))
        self.screen.blit(text_surface, (config.FIELD_MARGIN, config.SCREEN_HEIGHT - 36))


def run() -> None:
    game = TankGame()
    game.run()
