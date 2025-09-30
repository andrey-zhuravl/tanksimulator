"""Panel implementation for individual metronome instances."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Optional, Sequence, Set

import pygame

from . import config
from .drawing import draw_nodes, draw_polygon
from .geometry import step_positions
from .node import Node
from .sound import create_click_sound


@dataclass
class PanelFonts:
    """Collection of fonts used when rendering a metronome panel."""

    title: pygame.font.Font
    value: pygame.font.Font
    small: pygame.font.Font
    number: pygame.font.Font


class MetronomePanel:
    """Interactive metronome contained within a rectangular region."""

    def __init__(self, index: int, rect: pygame.Rect, fonts: PanelFonts) -> None:
        self.index = index
        self.rect = rect
        self.fonts = fonts

        self.enabled = False
        self.is_running = False
        self.num_steps = config.DEFAULT_NUM_STEPS
        self.sequence_duration = config.SEQUENCE_DURATION_SECONDS
        self.time_per_step = self.sequence_duration / self.num_steps
        self.current_step = self.num_steps - 1
        self.last_step_time = time.time()
        self.active_nodes: Set[int] = {0, 4, 7}

        self.first_frequency = config.DEFAULT_FIRST_FREQUENCY
        self.other_frequency = config.DEFAULT_OTHER_FREQUENCY
        self.click_sound_first = create_click_sound(frequency=self.first_frequency)
        self.click_sound = create_click_sound(frequency=self.other_frequency)

        self._compute_layout()
        self.nodes: Sequence[Node] = step_positions(
            self.circle_center, self.circle_radius, self.num_steps
        )

    # ------------------------------------------------------------------
    # Geometry and layout

    def _compute_layout(self) -> None:
        header_height = 48
        controls_height = 92
        usable_height = max(40, self.rect.height - header_height - controls_height)

        self.circle_radius = max(42, min(self.rect.width, usable_height) // 2 - 8)
        circle_center_y = self.rect.y + header_height + usable_height // 2
        self.circle_center = (self.rect.centerx, circle_center_y)

        control_top = self.rect.bottom - controls_height + 10
        button_w = 26
        button_h = 24
        right_button_x = self.rect.right - 16 - button_w
        left_button_x = self.rect.x + 16

        row_spacing = button_h + 8
        row0_y = control_top
        row1_y = control_top + row_spacing
        row2_y = control_top + row_spacing * 2

        self.step_minus_rect = pygame.Rect(left_button_x, row0_y, button_w, button_h)
        self.step_plus_rect = pygame.Rect(right_button_x, row0_y, button_w, button_h)

        self.first_minus_rect = pygame.Rect(left_button_x, row1_y, button_w, button_h)
        self.first_plus_rect = pygame.Rect(right_button_x, row1_y, button_w, button_h)

        self.other_minus_rect = pygame.Rect(left_button_x, row2_y, button_w, button_h)
        self.other_plus_rect = pygame.Rect(right_button_x, row2_y, button_w, button_h)

        checkbox_size = 22
        self.checkbox_rect = pygame.Rect(
            self.rect.x + 16,
            self.rect.y + 14,
            checkbox_size,
            checkbox_size,
        )

    def _rebuild_nodes(self) -> None:
        self.nodes = step_positions(self.circle_center, self.circle_radius, self.num_steps)
        self.current_step = min(self.current_step, self.num_steps - 1)
        self.active_nodes = {idx for idx in self.active_nodes if idx < self.num_steps}
        if not self.active_nodes:
            self.active_nodes = {0}

    # ------------------------------------------------------------------
    # Rendering

    def draw(self, surface: pygame.Surface) -> None:
        background = config.PANEL_BACKGROUND if self.enabled else config.PANEL_BACKGROUND_DISABLED
        pygame.draw.rect(surface, background, self.rect, border_radius=12)

        border_color = (
            config.PANEL_BORDER_ACTIVE if self.is_running and self.enabled else config.PANEL_BORDER_COLOR
        )
        pygame.draw.rect(surface, border_color, self.rect, width=2, border_radius=12)

        self._draw_header(surface)
        self._draw_circle(surface)
        self._draw_controls(surface)

        if not self.enabled:
            overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            surface.blit(overlay, self.rect)

    def _draw_header(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(
            surface,
            config.CONTROL_SURFACE_COLOR,
            pygame.Rect(self.rect.x + 10, self.rect.y + 8, self.rect.width - 20, 34),
            border_radius=10,
        )

        pygame.draw.rect(surface, config.TEXT_COLOR, self.checkbox_rect, width=2, border_radius=4)
        if self.enabled:
            inner = self.checkbox_rect.inflate(-6, -6)
            pygame.draw.rect(surface, config.ACCENT_COLOR, inner, border_radius=3)

        title = self.fonts.title.render(f"Метроном {self.index + 1}", True, config.TEXT_COLOR)
        title_rect = title.get_rect()
        title_rect.x = self.checkbox_rect.right + 10
        title_rect.centery = self.checkbox_rect.centery
        surface.blit(title, title_rect)

        status_text = "ВКЛ" if self.enabled else "ВЫКЛ"
        status_surface = self.fonts.small.render(status_text, True, config.SUBTLE_TEXT_COLOR)
        status_rect = status_surface.get_rect()
        status_rect.right = self.rect.right - 18
        status_rect.centery = self.checkbox_rect.centery
        surface.blit(status_surface, status_rect)

    def _draw_circle(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(surface, config.CONTROL_SURFACE_COLOR, self.circle_center, self.circle_radius + 10)
        pygame.draw.circle(surface, config.BACKGROUND_COLOR, self.circle_center, self.circle_radius + 8)

        draw_polygon(surface, self.nodes, self.active_nodes)
        draw_nodes(surface, self.nodes, self.active_nodes, self.current_step)

        number_surface = self.fonts.number.render(str(self.num_steps), True, config.SUBTLE_TEXT_COLOR)
        number_rect = number_surface.get_rect(center=self.circle_center)
        surface.blit(number_surface, number_rect)

    def _draw_controls(self, surface: pygame.Surface) -> None:
        control_area = pygame.Rect(
            self.rect.x + 10,
            self.step_minus_rect.y - 12,
            self.rect.width - 20,
            self.rect.bottom - (self.step_minus_rect.y - 12) - 12,
        )
        pygame.draw.rect(surface, config.CONTROL_SURFACE_COLOR, control_area, border_radius=10)

        rows = (
            ("Шаги", str(self.num_steps), self.step_minus_rect, self.step_plus_rect),
            (
                "1-й звук",
                f"{self.first_frequency} Гц",
                self.first_minus_rect,
                self.first_plus_rect,
            ),
            (
                "Остальные",
                f"{self.other_frequency} Гц",
                self.other_minus_rect,
                self.other_plus_rect,
            ),
        )

        for label, value, minus_rect, plus_rect in rows:
            self._draw_control_row(surface, label, value, minus_rect, plus_rect)

    def _draw_control_row(
        self,
        surface: pygame.Surface,
        label: str,
        value: str,
        minus_rect: pygame.Rect,
        plus_rect: pygame.Rect,
    ) -> None:
        pygame.draw.rect(surface, config.BUTTON_COLOR, minus_rect, border_radius=6)
        pygame.draw.rect(surface, config.BUTTON_COLOR, plus_rect, border_radius=6)

        minus_text = self.fonts.value.render("−", True, config.TEXT_COLOR)
        minus_rect_text = minus_text.get_rect(center=minus_rect.center)
        surface.blit(minus_text, minus_rect_text)

        plus_text = self.fonts.value.render("+", True, config.TEXT_COLOR)
        plus_rect_text = plus_text.get_rect(center=plus_rect.center)
        surface.blit(plus_text, plus_rect_text)

        label_surface = self.fonts.small.render(label, True, config.SUBTLE_TEXT_COLOR)
        label_rect = label_surface.get_rect()
        label_rect.left = minus_rect.right + 8
        label_rect.centery = minus_rect.centery - 10
        surface.blit(label_surface, label_rect)

        value_surface = self.fonts.value.render(value, True, config.TEXT_COLOR)
        value_rect = value_surface.get_rect()
        value_rect.left = minus_rect.right + 8
        value_rect.centery = minus_rect.centery + 10
        surface.blit(value_surface, value_rect)

    # ------------------------------------------------------------------
    # Interaction

    def handle_click(self, position: tuple[int, int]) -> None:
        if not self.rect.collidepoint(position):
            return

        if self.checkbox_rect.collidepoint(position):
            self.enabled = not self.enabled
            if not self.enabled:
                self.stop()
            return

        if self._handle_button(position):
            return

        self._handle_node_toggle(position)

    def _handle_button(self, position: tuple[int, int]) -> bool:
        if self.step_minus_rect.collidepoint(position):
            self._change_steps(-1)
            return True
        if self.step_plus_rect.collidepoint(position):
            self._change_steps(1)
            return True
        if self.first_minus_rect.collidepoint(position):
            self._change_first_frequency(-config.FREQUENCY_STEP)
            return True
        if self.first_plus_rect.collidepoint(position):
            self._change_first_frequency(config.FREQUENCY_STEP)
            return True
        if self.other_minus_rect.collidepoint(position):
            self._change_other_frequency(-config.FREQUENCY_STEP)
            return True
        if self.other_plus_rect.collidepoint(position):
            self._change_other_frequency(config.FREQUENCY_STEP)
            return True
        return False

    def _handle_node_toggle(self, position: tuple[int, int]) -> None:
        for node in self.nodes:
            if math.dist(position, node.position) <= config.NODE_RADIUS + 6:
                if node.index in self.active_nodes:
                    self.active_nodes.remove(node.index)
                else:
                    self.active_nodes.add(node.index)
                if not self.active_nodes:
                    self.active_nodes = {node.index}
                return

    # ------------------------------------------------------------------
    # State changes

    def _change_steps(self, delta: int) -> None:
        new_steps = max(config.MIN_STEPS, min(config.MAX_STEPS, self.num_steps + delta))
        if new_steps == self.num_steps:
            return

        self.num_steps = new_steps
        self.time_per_step = self.sequence_duration / self.num_steps
        self._rebuild_nodes()
        self.last_step_time = time.time()

    def _change_first_frequency(self, delta: int) -> None:
        new_value = max(config.MIN_FREQUENCY, min(config.MAX_FREQUENCY, self.first_frequency + delta))
        if new_value == self.first_frequency:
            return

        self.first_frequency = new_value
        self.click_sound_first = create_click_sound(frequency=self.first_frequency)

    def _change_other_frequency(self, delta: int) -> None:
        new_value = max(config.MIN_FREQUENCY, min(config.MAX_FREQUENCY, self.other_frequency + delta))
        if new_value == self.other_frequency:
            return

        self.other_frequency = new_value
        self.click_sound = create_click_sound(frequency=self.other_frequency)

    # ------------------------------------------------------------------
    # Playback

    def start(self, now: Optional[float] = None) -> None:
        if not self.enabled:
            return
        self.is_running = True
        self.time_per_step = self.sequence_duration / self.num_steps
        current_time = now if now is not None else time.time()
        self.last_step_time = current_time - self.time_per_step
        self.current_step = self.num_steps - 1

    def stop(self) -> None:
        self.is_running = False

    def update(self, now: float) -> None:
        if not (self.enabled and self.is_running):
            return

        if now - self.last_step_time < self.time_per_step:
            return

        self.current_step = (self.current_step + 1) % self.num_steps
        self.last_step_time = now

        if self.current_step in self.active_nodes:
            if self.current_step == 0:
                self.click_sound_first.play()
            else:
                self.click_sound.play()

