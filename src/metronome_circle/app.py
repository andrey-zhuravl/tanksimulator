"""Main application class orchestrating multiple metronome panels."""

from __future__ import annotations

import time
from typing import List

import pygame

from . import config
from .overlay import draw_overlay
from .panel import MetronomePanel, PanelFonts


class MetronomeApp:
    """Interactive application presenting nine independent metronomes."""

    def __init__(self) -> None:
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=1)

        self.screen = pygame.display.set_mode(config.WINDOW_SIZE)
        pygame.display.set_caption("Мульти-метроном")

        self.clock = pygame.time.Clock()

        fonts = PanelFonts(
            title=pygame.font.SysFont("arial", 18, bold=True),
            value=pygame.font.SysFont("arial", 18),
            small=pygame.font.SysFont("arial", 14),
            number=pygame.font.SysFont("arial", 34, bold=True),
        )

        self.instructions_font = pygame.font.SysFont("arial", 16)

        self.panels: List[MetronomePanel] = []
        self._create_panels(fonts)

        self.running = True
        self.is_running = False

    def _create_panels(self, fonts: PanelFonts) -> None:
        index = 0
        for row in range(config.GRID_ROWS):
            for col in range(config.GRID_COLS):
                x = config.WINDOW_MARGIN + col * (config.PANEL_WIDTH + config.GRID_GAP)
                y = config.WINDOW_MARGIN + row * (config.PANEL_HEIGHT + config.GRID_GAP)
                rect = pygame.Rect(x, y, config.PANEL_WIDTH, config.PANEL_HEIGHT)
                self.panels.append(MetronomePanel(index=index, rect=rect, fonts=fonts))
                index += 1

    def run(self) -> None:
        """Run the main event loop."""

        while self.running:
            self.clock.tick(60)
            self._handle_events()
            now = time.time()
            for panel in self.panels:
                panel.update(now)
            self._render()

        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_key(event)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_mouse(event.pos)

    def _handle_key(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_SPACE:
            self._toggle_playback()

    def _toggle_playback(self) -> None:
        self.is_running = not self.is_running
        now = time.time()

        if self.is_running:
            for panel in self.panels:
                if panel.enabled:
                    panel.start(now)
        else:
            for panel in self.panels:
                panel.stop()

    def _handle_mouse(self, position: tuple[int, int]) -> None:
        for panel in self.panels:
            panel.handle_click(position)
            if self.is_running and panel.enabled and not panel.is_running:
                panel.start(time.time())

    def _render(self) -> None:
        self.screen.fill(config.BACKGROUND_COLOR)

        for panel in self.panels:
            panel.draw(self.screen)

        draw_overlay(
            self.screen,
            self.instructions_font,
            (
                "Пробел — запуск/стоп включенных метрономов",
                "ЛКМ по чекбоксу — включить/выключить панель",
                "ЛКМ по точкам — акценты",
                "± — изменить шаги и частоты",
            ),
        )

        pygame.display.flip()
