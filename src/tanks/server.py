from __future__ import annotations

import json
import socket
import time
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import pygame

from . import config
from .tank import Tank, TankState


@dataclass
class ClientInfo:
    address: Tuple[str, int]
    team: str
    last_seen: float = field(default_factory=lambda: time.time())


class TankGameServer:
    def __init__(self, host: str = "0.0.0.0", port: int = config.DEFAULT_SERVER_PORT) -> None:
        self.host = host
        self.port = port
        self.tick_rate = config.SERVER_TICK_RATE
        self.broadcast_rate = config.STATE_BROADCAST_RATE

        pygame.init()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.socket.setblocking(False)

        self.clients: Dict[Tuple[str, int], ClientInfo] = {}
        self.team_tanks: Dict[str, List[Tank]] = {"player": [], "enemy": []}
        self.controls: Dict[str, Dict[str, Dict[str, bool]]] = {
            "player": {},
            "enemy": {},
        }

        self._create_teams()

        self.running = True
        self.last_broadcast = 0.0

    def _create_teams(self) -> None:
        spacing = (config.SCREEN_WIDTH - 2 * config.FIELD_MARGIN) / 6
        y_player = config.SCREEN_HEIGHT * 0.75
        y_enemy = config.SCREEN_HEIGHT * 0.25

        for index in range(5):
            x = config.FIELD_MARGIN + spacing * (index + 1)
            player_tank = Tank(
                position=pygame.math.Vector2(x, y_player),
                angle=270,
                turret_angle=270,
                color=config.PLAYER_TANK_COLOR,
                turret_color=config.TURRET_COLOR,
                identifier=f"player_{index}",
                is_player=(index == 0),
            )
            enemy_tank = Tank(
                position=pygame.math.Vector2(x, y_enemy),
                angle=90,
                turret_angle=90,
                color=config.ENEMY_TANK_COLOR,
                turret_color=config.ENEMY_TANK_COLOR,
                identifier=f"enemy_{index}",
            )
            self.team_tanks["player"].append(player_tank)
            self.team_tanks["enemy"].append(enemy_tank)

    def run(self) -> None:
        print(f"Tank server listening on {self.host}:{self.port}")
        previous_time = time.perf_counter()
        while self.running:
            now = time.perf_counter()
            dt = now - previous_time
            previous_time = now

            self._receive_messages()
            self._apply_controls(dt)
            self._update_world(dt)

            if now - self.last_broadcast >= 1.0 / self.broadcast_rate:
                self._broadcast_state(now)
                self.last_broadcast = now

            sleep_duration = max(0.0, (1.0 / self.tick_rate) - (time.perf_counter() - now))
            if sleep_duration > 0:
                time.sleep(sleep_duration)

    def _receive_messages(self) -> None:
        while True:
            try:
                payload, address = self.socket.recvfrom(65535)
            except BlockingIOError:
                break

            try:
                message = json.loads(payload.decode("utf-8"))
            except json.JSONDecodeError:
                continue

            message_type = message.get("type")
            if message_type == "join":
                self._handle_join(message, address)
            elif message_type == "input":
                self._handle_input(message, address)

    def _handle_join(self, message: dict, address: Tuple[str, int]) -> None:
        team = message.get("team", "player")
        if team not in self.team_tanks:
            response = {"type": "error", "message": f"unknown team '{team}'"}
            self.socket.sendto(json.dumps(response).encode("utf-8"), address)
            return

        client = ClientInfo(address=address, team=team)
        self.clients[address] = client
        print(f"Client {address} joined as {team}")

        tanks = [tank.identifier for tank in self.team_tanks[team]]
        response = {"type": "joined", "team": team, "tanks": tanks}
        self.socket.sendto(json.dumps(response).encode("utf-8"), address)

    def _handle_input(self, message: dict, address: Tuple[str, int]) -> None:
        client = self.clients.get(address)
        if not client:
            return

        team = message.get("team")
        if team != client.team:
            return

        commands = message.get("commands", {})
        team_controls = self.controls.setdefault(team, {})
        for tank_id, control in commands.items():
            team_controls[tank_id] = {
                "move_forward": bool(control.get("move_forward", False)),
                "move_backward": bool(control.get("move_backward", False)),
                "rotate_left": bool(control.get("rotate_left", False)),
                "rotate_right": bool(control.get("rotate_right", False)),
                "turret_left": bool(control.get("turret_left", False)),
                "turret_right": bool(control.get("turret_right", False)),
                "fire": bool(control.get("fire", False)),
            }

        client.last_seen = time.time()

    def _apply_controls(self, dt: float) -> None:
        for team, tanks in self.team_tanks.items():
            team_controls = self.controls.get(team, {})
            for tank in tanks:
                control = team_controls.get(tank.identifier or "", {})
                if control.get("move_forward"):
                    tank.move_forward(dt)
                if control.get("move_backward"):
                    tank.move_backward(dt)
                if control.get("rotate_left"):
                    tank.rotate_left(dt)
                if control.get("rotate_right"):
                    tank.rotate_right(dt)
                if control.get("turret_left"):
                    tank.rotate_turret_left(dt)
                if control.get("turret_right"):
                    tank.rotate_turret_right(dt)
                if control.get("fire"):
                    tank.fire()

    def _update_world(self, dt: float) -> None:
        for tanks in self.team_tanks.values():
            for tank in tanks:
                tank.update(dt)

    def _collect_state(self) -> List[TankState]:
        snapshot: List[TankState] = []
        for team, tanks in self.team_tanks.items():
            for tank in tanks:
                snapshot.append(tank.to_state(team))
        return snapshot

    def _broadcast_state(self, timestamp: float) -> None:
        state_payload = {
            "type": "state",
            "timestamp": timestamp,
            "tanks": [tank_state.to_dict() for tank_state in self._collect_state()],
        }
        encoded = json.dumps(state_payload).encode("utf-8")

        expired_clients = []
        for address, client in self.clients.items():
            if time.time() - client.last_seen > config.CLIENT_TIMEOUT:
                expired_clients.append(address)
                continue
            self.socket.sendto(encoded, address)

        for address in expired_clients:
            del self.clients[address]
            print(f"Removed inactive client {address}")


def run() -> None:
    TankGameServer().run()
