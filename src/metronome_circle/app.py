"""Main application class for the metronome circle."""

from __future__ import annotations

import math
import time
from typing import Set, Tuple

import pygame

from . import config
from .drawing import draw_nodes, draw_polygon
from .geometry import step_positions
from .overlay import draw_overlay
from .sound import create_click_sound


class MetronomeApp:
    """Interactive metronome rendered as a circular sequencer."""

    def __init__(self) -> None:
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=1)

        self.screen = pygame.display.set_mode(config.WINDOW_SIZE)
        pygame.display.set_caption("16-Step Rhythm Graph")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 220, bold=True)
        self.hints_font = pygame.font.SysFont("arial", 20)

        centre = (config.WINDOW_SIZE[0] // 2, config.WINDOW_SIZE[1] // 2)
        circle_radius = min(config.WINDOW_SIZE) // 2 - 80
        self.nodes = step_positions(centre, circle_radius, config.NUM_STEPS)

        self.active_nodes: Set[int] = {0, 4, 7, 11}
        self.current_step = 0
        self.is_running = False
        self.sequence_duration = config.SEQUENCE_DURATION_SECONDS
        self.time_per_step = self.sequence_duration / config.NUM_STEPS
        self.last_step_time = time.time()

        self.click_sound = create_click_sound()
        self.click_sound_first = create_click_sound(
            frequency=960, duration_ms=90, volume=0.8
        )

        self.running = True

    def run(self) -> None:
        """Run the main event loop."""

        while self.running:
            self.clock.tick(60)
            self._handle_events()

            if self.is_running:
                self._advance_step()

            self._render()

        pygame.quit()

    def _handle_events(self) -> None:
        """Handle pygame events."""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_key(event)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_mouse(event.pos)

    def _handle_key(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_SPACE:
            self.is_running = not self.is_running
            self.last_step_time = time.time()
        elif event.key == pygame.K_UP:
            self.sequence_duration = max(1.0, self.sequence_duration - 0.1)
            self._update_step_duration()
        elif event.key == pygame.K_DOWN:
            self.sequence_duration = min(3.0, self.sequence_duration + 0.1)
            self._update_step_duration()

    def _handle_mouse(self, position: Tuple[int, int]) -> None:
        for node in self.nodes:
            if math.dist(position, node.position) <= config.NODE_RADIUS + 4:
                if node.index in self.active_nodes:
                    self.active_nodes.remove(node.index)
                else:
                    self.active_nodes.add(node.index)
                break

    def _advance_step(self) -> None:
        now = time.time()
        if now - self.last_step_time < self.time_per_step:
            return

        self.current_step = (self.current_step + 1) % config.NUM_STEPS
        self.last_step_time = now

        if self.current_step in self.active_nodes:
            if self.current_step == 0:
                self.click_sound_first.play()
            else:
                self.click_sound.play()

    def _render(self) -> None:
        self.screen.fill(config.BACKGROUND_COLOR)

        status = "Играет" if self.is_running else "Пауза"
        hints = (
            "Пробел — старт/стоп",
            "Клик — акцент",
            "↑/↓ — скорость",
            f"Цикл: {self.sequence_duration:.2f} с",
            f"Статус: {status}",
        )
        draw_overlay(self.screen, self.font, self.hints_font, hints)
        draw_polygon(self.screen, self.nodes, self.active_nodes)
        draw_nodes(self.screen, self.nodes, self.active_nodes, self.current_step)

        pygame.display.flip()

    def _update_step_duration(self) -> None:
        self.time_per_step = self.sequence_duration / config.NUM_STEPS
