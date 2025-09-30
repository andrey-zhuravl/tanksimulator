"""Rendering helpers for the metronome circle application."""

from __future__ import annotations

from typing import Iterable, Sequence

import pygame

from . import config
from .node import Node


def draw_nodes(
    surface: pygame.Surface,
    nodes: Sequence[Node],
    active_nodes: Iterable[int],
    current_step: int,
) -> None:
    """Render the circular graph with highlights for active and current nodes."""

    active_set = set(active_nodes)

    for node in nodes:
        node_color = config.DEFAULT_NODE_COLOR
        outline_color = config.CIRCLE_COLOR

        if node.index in active_set:
            node_color = config.ACCENT_COLOR
        if node.index == current_step:
            outline_color = config.CURRENT_STEP_COLOR

        pygame.draw.circle(
            surface, outline_color, node.position, config.NODE_RADIUS + 4
        )
        pygame.draw.circle(surface, node_color, node.position, config.NODE_RADIUS)
        pygame.draw.circle(
            surface,
            config.BACKGROUND_COLOR,
            node.position,
            config.NODE_RADIUS,
            config.OUTLINE_WIDTH,
        )


def draw_polygon(
    surface: pygame.Surface, nodes: Sequence[Node], active_nodes: Iterable[int]
) -> None:
    """Draw a polygon connecting active nodes in order of the sequence."""

    active_indices = [node_index for node_index in sorted(set(active_nodes))]
    if len(active_indices) < 2:
        return

    points = [nodes[index].position for index in active_indices]
    pygame.draw.lines(surface, config.POLYGON_COLOR, True, points, 3)
