"""Overlay rendering helpers for UI elements."""

from __future__ import annotations

from typing import Iterable, Tuple

import pygame

from . import config


def draw_overlay(
    surface: pygame.Surface,
    font: pygame.font.Font,
    hints_font: pygame.font.Font,
    hints: Iterable[str],
) -> None:
    """Draw UI text elements such as the centre number and control hints."""

    width, height = surface.get_size()
    hints_tuple: Tuple[str, ...] = tuple(hints)

    number_text = font.render(str(config.NUM_STEPS), True, (70, 70, 80))
    number_rect = number_text.get_rect(center=(width // 2, height // 2))
    surface.blit(number_text, number_rect)

    for index, hint in enumerate(hints_tuple):
        hint_surface = hints_font.render(hint, True, config.TEXT_COLOR)
        surface.blit(hint_surface, (20, 20 + index * 24))
