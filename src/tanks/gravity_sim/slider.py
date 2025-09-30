"""UI slider control used for tweaking settings."""

from __future__ import annotations

from typing import Callable

import pygame

from .constants import SLIDER_HANDLE_COLOR, SLIDER_TRACK_COLOR, TEXT_COLOR
from .settings import SimulationSettings


class Slider:
    """A horizontal slider UI component."""

    def __init__(
        self,
        label: str,
        attr: str | None,
        settings: SimulationSettings,
        min_value: float,
        max_value: float,
        position: tuple[int, int],
        length: int,
        postprocess: Callable[[float], float],
        formatter: Callable[[float], str],
        getter: Callable[[], float] | None = None,
        setter: Callable[[float], None] | None = None,
    ) -> None:
        self.label = label
        self.attr = attr
        self.settings = settings
        self.min_value = min_value
        self.max_value = max_value
        self.position = position
        self.length = length
        self.postprocess = postprocess
        self.formatter = formatter
        self.dragging = False
        self.handle_radius = 8
        if attr is None:
            if getter is None or setter is None:
                raise ValueError("Custom sliders require getter and setter callables")
            self._value_getter = getter
            self._value_setter = setter
        else:
            self._value_getter = lambda: getattr(self.settings, attr)
            self._value_setter = lambda value: setattr(self.settings, attr, value)

    @property
    def value(self) -> float:
        return self._value_getter()

    def set_value(self, raw_value: float) -> None:
        clamped = max(self.min_value, min(self.max_value, raw_value))
        value = self.postprocess(clamped)
        self._value_setter(value)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._handle_rect().collidepoint(event.pos) or self._track_rect().collidepoint(event.pos):
                self.dragging = True
                self._update_from_x(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_from_x(event.pos[0])

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        label_surface = font.render(self.label, True, TEXT_COLOR)
        surface.blit(label_surface, (self.position[0], self.position[1] - 18))

        track_rect = self._track_rect()
        pygame.draw.rect(surface, SLIDER_TRACK_COLOR, track_rect, border_radius=4)

        handle_rect = self._handle_rect()
        pygame.draw.circle(surface, SLIDER_HANDLE_COLOR, handle_rect.center, self.handle_radius)

        value_surface = font.render(self.formatter(self.value), True, TEXT_COLOR)
        surface.blit(value_surface, (self.position[0] + self.length + 16, self.position[1] - 10))

    def _track_rect(self) -> pygame.Rect:
        return pygame.Rect(self.position[0], self.position[1], self.length, 6)

    def _handle_rect(self) -> pygame.Rect:
        current = max(self.min_value, min(self.max_value, self.value))
        ratio = (current - self.min_value) / (self.max_value - self.min_value)
        center_x = self.position[0] + ratio * self.length
        center_y = self.position[1] + 3
        return pygame.Rect(
            int(center_x) - self.handle_radius,
            int(center_y) - self.handle_radius,
            self.handle_radius * 2,
            self.handle_radius * 2,
        )

    def _update_from_x(self, x: int) -> None:
        ratio = (x - self.position[0]) / self.length
        ratio = max(0.0, min(1.0, ratio))
        raw_value = self.min_value + ratio * (self.max_value - self.min_value)
        self.set_value(raw_value)
