"""Overlay rendering helpers for UI elements."""

from __future__ import annotations

from typing import Iterable

import pygame

from . import config


def draw_overlay(surface: pygame.Surface, font: pygame.font.Font, hints: Iterable[str]) -> None:
    """Draw control hints in the lower-left corner of the screen."""

    hints_tuple = tuple(hints)
    height = surface.get_height()

    for index, hint in enumerate(reversed(hints_tuple)):
        text_surface = font.render(hint, True, config.SUBTLE_TEXT_COLOR)
        text_rect = text_surface.get_rect()
        text_rect.x = 20
        text_rect.y = height - 20 - (index + 1) * (text_rect.height + 4)
        surface.blit(text_surface, text_rect)
