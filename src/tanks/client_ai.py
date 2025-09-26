from __future__ import annotations

import json
import math
import socket
import time
from typing import Dict, List

from . import config
from .tank import TankState


class AITankClient:
    def __init__(
        self,
        host: str = config.DEFAULT_SERVER_HOST,
        port: int = config.DEFAULT_SERVER_PORT,
        team: str = "enemy",
    ) -> None:
        self.team = team
        self.server = (host, port)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect(self.server)
        self.socket.setblocking(False)

        self.state: List[TankState] = []
        self.owned_tanks: List[str] = []
        self.running = True

        self._send_join()

    def _send_join(self) -> None:
        payload = {"type": "join", "team": self.team, "client": "ai"}
        self.socket.send(json.dumps(payload).encode("utf-8"))

    def run(self) -> None:
        update_interval = 1.0 / config.AI_UPDATE_RATE
        while self.running:
            start = time.perf_counter()
            self._receive_messages()
            self._send_commands()
            elapsed = time.perf_counter() - start
            sleep_time = max(0.0, update_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

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
        elif message_type == "state":
            self.state = [TankState.from_dict(data) for data in message.get("tanks", [])]

    def _send_commands(self) -> None:
        if not self.owned_tanks or not self.state:
            return

        friendlies = [tank for tank in self.state if tank.team == self.team and tank.identifier in self.owned_tanks]
        enemies = [tank for tank in self.state if tank.team != self.team]
        if not friendlies or not enemies:
            return

        commands: Dict[str, Dict[str, bool]] = {}
        for friendly in friendlies:
            target = self._select_target(friendly, enemies)
            command = self._compute_command(friendly, target)
            commands[friendly.identifier] = command

        payload = {"type": "input", "team": self.team, "commands": commands, "timestamp": time.time()}
        self.socket.send(json.dumps(payload).encode("utf-8"))

    def _select_target(self, friendly: TankState, enemies: List[TankState]) -> TankState:
        fx, fy = friendly.x, friendly.y
        return min(enemies, key=lambda enemy: (enemy.x - fx) ** 2 + (enemy.y - fy) ** 2)

    def _compute_command(self, friendly: TankState, target: TankState) -> Dict[str, bool]:
        command = {
            "move_forward": False,
            "move_backward": False,
            "rotate_left": False,
            "rotate_right": False,
            "turret_left": False,
            "turret_right": False,
            "fire": False,
        }

        desired_angle = math.degrees(math.atan2(target.y - friendly.y, target.x - friendly.x)) % 360
        angle_diff = (desired_angle - friendly.turret_angle + 540) % 360 - 180

        if angle_diff > 5:
            command["turret_right"] = True
        elif angle_diff < -5:
            command["turret_left"] = True
        else:
            command["fire"] = True

        # Slowly rotate the hull to face the target as well
        hull_diff = (desired_angle - friendly.angle + 540) % 360 - 180
        if hull_diff > 10:
            command["rotate_right"] = True
        elif hull_diff < -10:
            command["rotate_left"] = True

        return command


def run() -> None:
    AITankClient().run()
