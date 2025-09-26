from __future__ import annotations

import json
import socket
import time
from typing import List, Optional

import pygame

from . import config
from .tank import TankState


class KeyboardTankClient:
    def __init__(
        self,
        host: str = config.DEFAULT_SERVER_HOST,
        port: int = config.DEFAULT_SERVER_PORT,
        team: str = "player",
    ) -> None:
        self.team = team
        self.server = (host, port)

        pygame.init()
        pygame.display.set_caption("Tank Simulator - Keyboard Client")
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 24)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect(self.server)
        self.socket.setblocking(False)

        self.running = True
        self.state: List[TankState] = []
        self.owned_tanks: List[str] = []
        self.active_tank: Optional[str] = None
        self.last_state_received: float = time.time()

        self._send_join()

    def _send_join(self) -> None:
        payload = {"type": "join", "team": self.team, "client": "keyboard"}
        self.socket.send(json.dumps(payload).encode("utf-8"))

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self._handle_events()
            self._receive_messages()
            self._send_input()
            self._draw()
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_TAB:
                    self._cycle_active_tank()

    def _receive_messages(self) -> None:
        while True:
            try:
                payload = self.socket.recv(65535)
            except BlockingIOError:
                break
            if not payload:
                break

            try:
                message = json.loads(payload.decode("utf-8"))
            except json.JSONDecodeError:
                continue

            self._handle_message(message)

    def _handle_message(self, message: dict) -> None:
        message_type = message.get("type")
        if message_type == "joined":
            self.owned_tanks = [str(tank_id) for tank_id in message.get("tanks", [])]
            if self.owned_tanks and self.active_tank not in self.owned_tanks:
                self.active_tank = self.owned_tanks[0]
        elif message_type == "state":
            tanks = [TankState.from_dict(data) for data in message.get("tanks", [])]
            self.state = tanks
            self.last_state_received = time.time()
            if not self.active_tank and self.owned_tanks:
                self.active_tank = self.owned_tanks[0]

    def _send_input(self) -> None:
        if not self.active_tank:
            return

        keys = pygame.key.get_pressed()
        command = {
            "move_forward": keys[pygame.K_w],
            "move_backward": keys[pygame.K_s],
            "rotate_left": keys[pygame.K_a],
            "rotate_right": keys[pygame.K_d],
            "turret_left": keys[pygame.K_q],
            "turret_right": keys[pygame.K_e],
            "fire": keys[pygame.K_SPACE],
        }

        payload = {
            "type": "input",
            "team": self.team,
            "commands": {self.active_tank: command},
            "timestamp": time.time(),
        }
        self.socket.send(json.dumps(payload).encode("utf-8"))

    def _draw(self) -> None:
        self.screen.fill(config.BACKGROUND_COLOR)
        self._draw_field()
        self._draw_tanks()
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

    def _draw_tanks(self) -> None:
        for tank in self.state:
            tank.draw(self.screen)

    def _draw_hud(self) -> None:
        status_lines = ["WASD - движение, Q/E - башня, SPACE - огонь", "TAB - переключение танка"]
        if self.active_tank:
            status_lines.append(f"Активный танк: {self.active_tank}")
        latency = time.time() - self.last_state_received
        status_lines.append(f"Запаздывание: {latency*1000:.0f} мс")

        for index, text in enumerate(status_lines):
            surface = self.font.render(text, True, (220, 220, 220))
            self.screen.blit(surface, (config.FIELD_MARGIN, config.SCREEN_HEIGHT - 36 - index * 28))

    def _cycle_active_tank(self) -> None:
        if not self.owned_tanks:
            return
        if self.active_tank not in self.owned_tanks:
            self.active_tank = self.owned_tanks[0]
            return
        current_index = self.owned_tanks.index(self.active_tank)
        next_index = (current_index + 1) % len(self.owned_tanks)
        self.active_tank = self.owned_tanks[next_index]


def run() -> None:
    KeyboardTankClient().run()
